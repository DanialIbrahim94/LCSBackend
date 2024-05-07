import json
import time
import requests

from woocommerce import API
from jotform import JotformAPIClient

from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings

from administrator.models import User, Coupons
from administrator.countries import countries_list
from forms.models import Form, Field, Submission


class WooCommerceAPI():
	api = None
	
	def __init__(self):
		self.api = API(
			url = settings.WOOCOMMERCE_URL,
			consumer_key = settings.WOOCOMMERCE_CONSUMER_KEY,
			consumer_secret = settings.WOOCOMMERCE_CONSUMER_SECRET,
			version = settings.WOOCOMMERCE_VERSION,
			wp_api = True
		)

	def get(self, request, params={}):
		response = self.api.get(request, params=params)
		return response

	def post(self, request, data, params={}):
		response = self.api.post(request, data, params=params)
		return response

	def get_orders(self, email):
		response = self.get('orders', params={'search': email}).json()
		filtered_orders = []
		while response:
			order = response.pop(0)
			if order and order['billing']['email'] == email and order.get('status') != 'completed':
				filtered_orders.append(order)

		return filtered_orders

	def get_customer(self, user):
		email = user.email
		customer = None
		response = self.get('customers', params={'search': email})

		if response.ok:
			customers = response.json()
			while customers:
				_customer = customers.pop()
				if _customer.get('email') == email:
					customer = _customer
					break

		return customer

	def order(self, user, amount):
		first_name, *last_name = user.fullName.split(' ')
		data = {
			"payment_method": settings.WOOCOMMERCE_PAYMENT_METHOD,
			"payment_method_title": settings.WOOCOMMERCE_PAYMENT_METHOD_TITLE,
			"set_paid": False,
			"line_items": [
				{
					"product_id": settings.WOOCOMMERCE_PRODUCT_ID,
					"variation_id": settings.WOOCOMMERCE_PRODUCT_VARIATIONS.get(amount),
					"quantity": 1
				}
			],
			"billing": {
				"first_name": first_name,
				"last_name": last_name[-1] if last_name else '',
				"address_1": user.address,
				"address_2": "",
				"city": "",
				"state": "",
				"postcode": "",
				"country": "",
				"email": user.email,
				"phone": user.phone
			},
		}
		customer = self.get_customer(user)
		if customer and customer.get('id'):
			data["customer_id"] = customer.get('id')

		response = self.post('orders', data)
		return response

	def set_order_status(self, order_id, status):
		return self.api.put(f'orders/{order_id}', {'status': status}).ok

	def verify_order(self, order_id):

		order = self.get(f'orders/{order_id}')
		if order.ok:
			_order = order.json()
			status = _order['status']
			if status == 'completed':
				return False, {'message': 'Order already processed!'}

			if status != 'processing':
				return False, {'message': 'The order has not been paid for yet.'}

			user_email = _order['billing']['email']
			wc_variations = settings.WOOCOMMERCE_PRODUCT_VARIATIONS
			amount = list(wc_variations.keys())[list(wc_variations.values()).index(_order['line_items'][0]['variation_id'])]

			qs = User.objects.filter(email=user_email)
			if qs.exists():
				user = qs.first()
				admin_user = User.objects.first()
				bulk_coupons = Coupons.objects.filter(user=admin_user)
				if bulk_coupons.count() < amount:
					return False, {'message': 'All coupons have been claimed. Please contact the administrators.'}

				is_ok = self.set_order_status(order_id, 'completed')
				if not is_ok:
					return False, {
						'message': '''
							Couldn\'t automatically complete the order thus we are not releasing the codes.\n
							Please contact the administrators of this site
						'''
					}

				coupons_ids = bulk_coupons.values_list('pk', flat=True)[:amount]
				Coupons.objects.filter(pk__in=coupons_ids).update(user=user)

				return True, {'is_valid': True}
			else:
				pass

		return False


class LeadsOrderAPI(WooCommerceAPI):
	product_id = 30183

	def order_leads(self, user, quantity):
		try:
			first_name, last_name = user.fullName.split(' ')
		except:
			first_name = user.fullName
			last_name = ""

		data = {
			"payment_method": settings.WOOCOMMERCE_PAYMENT_METHOD,
			"payment_method_title": settings.WOOCOMMERCE_PAYMENT_METHOD_TITLE,
			"set_paid": False,
			"line_items": [
				{
					"product_id": self.product_id,  # Leads product ID
					"quantity": quantity
				}
			],
			"billing": {
				"first_name": first_name,
				"last_name": last_name,
				"address_1": user.address,
				"address_2": "",
				"city": "",
				"state": "",
				"postcode": "",
				"country": "US",
				"email": user.email,
				"phone": user.phone
			},
		}
		customer = self.get_customer(user)
		if customer and customer.get('id'):
			data["customer_id"] = customer.get('id')

		response = self.post('orders', data)
		return response

	def get_orders(self, email):
		response = self.get('orders', params={'search': email}).json()
		filtered_orders = []
		while response:
			order = response.pop(0)
			if order and order['billing']['email'] == email and order.get('status') != 'completed':
				if order['line_items'][0]['product_id'] == self.product_id:
					filtered_orders.append(order)

		return filtered_orders

	def verify_order(self, order_id):
		order = self.get(f'orders/{order_id}')
		if order.ok:
			_order = order.json()
			status = _order['status']
			if status == 'completed':
				return False, {'message': 'Order already processed!'}

			if status != 'processing':
				return False, {'message': 'The order has not been paid for yet.'}

			user_email = _order['billing']['email']
			line_items = _order['line_items']
			total_quantity = sum(item['quantity'] for item in line_items)

			if any(item['product_id'] == 30183 for item in line_items):
				# If the leads product is included in the order
				user = User.objects.filter(email=user_email).first()
				if user:
					is_ok = self.set_order_status(order_id, 'completed')
					if not is_ok:
						print('Couldn\'t automatically complete the order thus we are not releasing the codes. Please contact the administrators of this site')
						return False, {
							'message': '''
								Couldn\'t automatically complete the order thus we are not releasing the codes.\n
								Please contact the administrators of this site
							'''
						}

					user.leads_count += total_quantity
					user.save()
					return True, {'is_valid': True}

		return False, {}


class JotformAPI():
	api = None
	def __init__(self):
		self.api = JotformAPIClient(settings.JOTFORM_API_KEY)

	def update_form_properties(self, formID, apiKey, properties):
		# Construct the API endpoint URL
		url = f"https://api.jotform.com/form/{formID}/properties?apiKey={apiKey}"

		# Construct the data payload for the PUT request
		# data = {"properties": properties}
		data = {
			"properties" : {
				"formType": "ClassicForm",
				"welcomePage": [properties],
				"emailValidation": "Yes"
			}
		}
		data_str = json.dumps(data)

		headers = {"Content-Type": "application/json"}

		response = requests.put(url, data=data_str, headers=headers)

		return response

	def get_form_welcome_page(self, formID):
		# Construct the API endpoint URL
		url = f"https://api.jotform.com/form/{formID}/properties?apiKey={settings.JOTFORM_API_KEY}"

		headers = {"Content-Type": "application/json"}

		response = requests.get(url, headers=headers)

		return response.json()['content'].get('welcomePage', None)

	def create_form(self, name, elements, welcome, verification_code, user):
		name= "<b style='color: #4a98d2;font-size: 64px;'>The $100</b> Hotel Saver Gift"
		description = 'You’re about to receive a $100 coupon that you can redeem and use at 1,000,000 worldwide hotels and resorts up to 2-years, once redeemed.\n'\
			'There is nothing to join, no blackout dates, no travel restrictions, and no timeshare presentations to attend.<br />\n'\
			'<b style="margin-bottom: 20px;">NO GIMMICKS, JUST SAVINGS</b> <br />\n'\
			'<small>You will be emailed with instructions how to use this within 1-minute once submitted</small>'
		questions = {}
		index = 1
		for value in elements:
			if value.get('required'):
				value['required'] = 'Yes' if value['required'] else 'No'

			if value.get('type') == 'control_address':
				# Country
				required = value.get('required', 'No')
				countries = countries_list.values()

				value['type'] = 'control_dropdown'
				value['options'] = '|'.join(countries)
				value['required'] = required

				questions[str(index)] = value
				index += 1
				# State, City
				value = {
					'type': 'control_input',
					'text': 'City, State',
					'required': required
				}
				questions[str(index)] = value

			questions[str(index)] = value
			index += 1

		form = Form.objects.create(
			name=name,
			description=description,
			user=user,
			verify_email=verification_code,
		)
		for index, question in questions.items():
			field = Field.objects.create(
				form=form,
				identifier=question.get('type'),
				label=question.get('text'),
				options=question.get('options'),
				required=(question.get('required')=='Yes'),
				position=index,
			)
			# Implement email verification

		if not form.fields.filter(identifier=Field.EMAIL_INPUT).exists():
			form.verify_email = False
			form.save()

		return form, True

	def update_form(self, name, elements, user):
		# build the questions dictionary
		questions = {}
		index = 1
		for value in elements:
			if value.get('type') == 'control_address':
				# Country
				required = value.get('required', 'No')
				countries = countries_list.values()

				value['type'] = 'control_dropdown'
				value['options'] = '|'.join(countries)
				value['required'] = required

				questions[str(index)] = value
				index += 1
				# State, City
				value = {
					'type': 'control_input',
					'text': 'City, State',
					'required': required
				}
				questions[str(index)] = value

			questions[str(index)] = {
				"type": value["type"],
				"text": value["text"],
				"required": "Yes" if value.get("required") else "No",
				# "name": f"Header{i+1}"
			}
			index += 1

		form = user.forms.first()
		form.fields.all().delete()
		for index, question in questions.items():
			field = Field.objects.create(
				form=form,
				identifier=question.get('type'),
				label=question.get('text'),
				options=question.get('options'),
				required=(question.get('required')=='Yes'),
				position=index,
			)
			# Implement email verification

		return form, True

	def get_submissions(self, form_slug):
		try:
			form = Form.objects.get(slug=form_slug)
			submissions = Submission.objects.filter(form__slug=form_slug)

			submission_data = []

			for submission in submissions:
				answers = dict(submission.data)
				org_answers = {}
				index = 2
				for key, value in answers.items():
					org_answers[f'{index}'] = {
						"text": f'{key}',
						"order": f'{index}',
						"answer": value
					}
					index += 1

				# answers now is like
				# {
				#     "Name": "adem",
				#     "email": "value"
				# }
				# how to convert it to be like

				# {
				#     "1": {
				#         "order": "1",
				#         "answer": {
				#             "first": "new",
				#             "last": "user"
				#         },
				#         "prettyFormat": "new user"
				#     },
				#     "3": {
				#         "order": "3",
				#         "text": "Birth Date",
				#         "type": "control_datetime",
				#         "answer": {
				#             "month": "04",
				#             "day": "16",
				#             "year": "2024",
				#             "datetime": "2024-04-16 00:00:00"
				#         },
				#         "prettyFormat": "04-16-2024-2024-04-16 00:00:00"
				#     },
				#     "4": {
				#         "order": "4",
				#         "text": "Type a question",
				#         "type": "control_email",
				#         "answer": "araariadem0@gmail.com"
				#     }
				# }

				submission_info = {
					"id": str(submission.id),
					"form_id": str(submission.form.id),
					"ip": "",  # You can add IP address if available
					"created_at": submission.date.strftime("%Y-%m-%d %H:%M:%S"),
					"status": "ACTIVE",  # Assuming all submissions are active
					"new": "1",  # Assuming all submissions are new
					"flag": "0",  # Assuming no flags
					"notes": "",  # Assuming no notes
					"updated_at": None,  # Assuming no updates
					"answers": org_answers
				}

				submission_data.append(submission_info)

			return submission_data

		except Form.DoesNotExist:
			# Handle form not found
			return None

	def get_form_data(self, form_slug):
		form = Form.objects.get(slug=form_slug)
		welcome_page = []
		form_questions = {}
		index = 1
		for field in form.fields.all():
			if field.identifier == Field.EMAIL_INPUT:
				form_questions[index] = {
					"identifier": field.identifier,
					"type": field.identifier,
					"text": field.label,
					"options": field.options,
					"required": 'Yes' if field.required else 'No',
					"verificationCode": 'Yes' if field.form.verify_email else 'No'
				}
			else:
				form_questions[index] = {
					"identifier": field.identifier,
					"type": field.identifier,
					"text": field.label,
					"options": field.options,
					"required": 'Yes' if field.required else 'No'
				}
			index += 1
		form_data = {
			'id': form_slug,
			'name': form.name,
			'questions': form_questions,
			'welcome_page': welcome_page
		}
		return form_data, True
