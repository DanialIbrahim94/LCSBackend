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

	def redeem_coupon(self, submission, product_id, referral_id=None):
		print(product_id)
		# Extract user information from the submission data
		data = submission.data
		email = submission._get_email()
		if len(submission._get_field('name', '').split(' ')) >= 2:
			first_name = submission._get_field('name', '').split(' ')[0]
			last_name = ' '.join(submission._get_field('name', '').split(' ')[1:])
		else:
			first_name = submission._get_field('name', '')
			last_name = ''
		country = submission._get_field('country', '')
		city = submission._get_field('city', '')
		state = submission._get_field('state', '')
		phone = submission._get_field('phone', '')
		birthday = submission._get_field('birthday', '')

		# Create a dummy user object for the purpose of order creation
		user_data = {
			'first_name': first_name,
			'last_name': last_name,
			'email': email,
			'country': country,
			'city': city,
			'state': state,
			'phone': phone,
			'birthday': birthday,
		}

		amount = 1
		coupon_code = submission.get_coupon()

		# Create an order using the extracted user data
		order_response = self.order(user_data, amount, product_id)

		if order_response.ok:
			order_data = order_response.json()
			order_id = order_data['id']

			if product_id == 1:
				# Apply the coupon to the order
				coupon_response = self.apply_coupon_to_order(order_id, coupon_code)

				if coupon_response.ok:
					self.set_order_status(order_id, 'completed')
					redirect_url = f"{settings.WOOCOMMERCE_URL}/thank-you/#{referral_id}/?order_key={order_data['order_key']}"
					return {"success": True, "coupon": coupon_code, "redirect_url": redirect_url}
				else:
					self.delete_order(order_id)
					# Handle error in applying coupon
					return {"success": False, "error": "Failed to apply coupon.", "details": coupon_response.json()}
			else:
				# Get the redirect URL
				redirect_url = f"{settings.WOOCOMMERCE_URL}/checkout/order-pay/{order_id}/?referralID={referral_id}&pay_for_order=true&key={order_data['order_key']}"
				return {"success": True, "coupon": coupon_code, "redirect_url": redirect_url}
		else:
			# Handle error in creating order
			return {"success": False, "error": "Failed to create order, please try again later or contact us for additional support!", "details": order_response.json()}

	def apply_coupon_to_order(self, order_id, coupon_code):
		data = {
			"coupon_lines": [
				{
					"code": coupon_code
				}
			]
		}
		response = self.api.put(f'orders/{order_id}', data)
		return response

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

	def get_customer(self, user, email=None):
		email = email or user.email
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

	def create_customer(self, user_data):
		data = {
			"email": user_data.get('email'),
			"first_name": user_data.get('first_name'),
			"last_name": user_data.get('last_name'),
			"billing": {
				"first_name": user_data.get('first_name'),
				"last_name": user_data.get('last_name'),
				"city": user_data.get('city'),
				"state": user_data.get('state'),
				"country": user_data.get('country'),
				"email": user_data.get('email'),
				"phone": user_data.get('phone')
			},
		}

		return self.post("customers", data).json()

	def order(self, user_data, amount, product_id):
		country = user_data.get('country', '')
		res = dict((v,k) for k,v in countries_list.items())
		country_code = res.get(country) if country and res else ''
		data = {
			"payment_method": settings.WOOCOMMERCE_PAYMENT_METHOD,
			"payment_method_title": settings.WOOCOMMERCE_PAYMENT_METHOD_TITLE,
			"set_paid": False,
			"line_items": [
				{
					"product_id": [settings.WOOCOMMERCE_PRODUCT_ID, 614, 610][product_id-1],
					"quantity": amount
				}
			],
			"billing": {
				"first_name": user_data.get('first_name', ''),
				"last_name": user_data.get('last_name', ''),
				"address_1": user_data.get('address', ''),
				"city": user_data.get('city', ''),
				"state": user_data.get('state', ''),
				"country": country_code,
				"email": user_data.get('email', ''),
				"phone": user_data.get('phone', '')
			},
		}
		email = user_data.get('email')
		customer = self.get_customer(None, email=email)
		if customer and customer.get('id'):
			data["customer_id"] = customer.get('id')

		# if not customer or not customer.get('id'):
		# 	print(self.create_customer(user_data))
		
		# customer = self.get_customer(None, email=email)
		# data["customer_id"] = customer.get('id')

		print(data)

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
			amount = 0

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

	def delete_order(self, order_id):
		return self.api.delete(f"orders/{order_id}").json()


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

	def create_form(self, name, elements, welcome, verification_code, logo_url, user):
		name= "<b style='color: #4a98d2;font-size: 64px;'>The $100</b> Hotel Saver Gift"
		description = '<span style="margin-bottom: 4px;">You’re about to receive a FREE coupon valued up to $100 in GUARANTEED hotel savings* BELOW the prices listed on Expedia, Priceline and many others.</span> <br />\n'\
			'<span style="margin-bottom: 4px;">You can use the savings on up to 1,000,000 worldwide hotels and resorts up to 2-years, once redeemed. There is nothing to join, no blackout dates, no travel restrictions, and no timeshare presentations to attend.</span> <br />\n'\
			'<b style="margin-bottom: 10px;">NO GIMMICKS, JUST SAVINGS!</b> <br />\n'\
			'The amount of savings will vary based on the time of year, the length of stay, the type of property and any special events going on in the area at the time of booking. <br />\n'
		questions = {}
		index = 1
		for value in elements:
			if value.get('required'):
				value['required'] = 'Yes' if value['required'] else 'No'

			if value.get('type') == 'control_address':
				# Country
				required = "Yes" if value.get("required") else "No"
				countries = countries_list.values()

				value['type'] = 'control_dropdown'
				value['options'] = '|'.join(countries)
				value['required'] = required

				questions[str(index)] = value
				index += 1
				# State, City
				value = {
					'type': 'control_input',
					'text': 'State',
					'required': required
				}
				questions[str(index)] = value
				index += 1

				# State, City
				value = {
					'type': 'control_input',
					'text': 'City',
					'required': required
				}
				questions[str(index)] = value

			questions[str(index)] = value
			index += 1

		form = Form.objects.create(
			user=user,
			name=name,
			description=description,
			verify_email=verification_code,
			logo_url=logo_url,
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

	def update_form(self, name, elements, logo_url, user):
		# build the questions dictionary
		questions = {}
		index = 1
		for value in elements:
			if value.get('type') == 'control_dropdown':
				# Country
				required = "Yes" if value.get("required") else "No"
				countries = countries_list.values()

				value['type'] = 'control_dropdown'
				value['options'] = '|'.join(countries)
				value['required'] = required

			elif value.get('type') == 'control_address':
				# Country
				required = "Yes" if value.get("required") else "No"
				countries = countries_list.values()

				value['type'] = 'control_dropdown'
				value['options'] = '|'.join(countries)
				value['required'] = required

				questions[str(index)] = value
				index += 1
				# State, City
				value = {
					'type': 'control_input',
					'text': 'State',
					'required': required
				}
				questions[str(index)] = value
				index += 1

				# State, City
				value = {
					'type': 'control_input',
					'text': 'City',
					'required': required
				}
				questions[str(index)] = value

			questions[str(index)] = {
				"type": value["type"],
				"text": value["text"],
				"options": value.get("options", ''),
				"required": "Yes" if value.get("required") else "No",
				# "name": f"Header{i+1}"
			}
			index += 1

		form = user.forms.first()
		form.logo_url = logo_url
		form.save()

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
				#	 "Name": "adem",
				#	 "email": "value"
				# }
				# how to convert it to be like

				# {
				#	 "1": {
				#		"order": "1",
				#		"answer": {
				#		"first": "new",
				#		"last": "user"
				#		},
				#		"prettyFormat": "new user"
				#	 },
				#	 "3": {
				#		"order": "3",
				#		"text": "Birth Date",
				#		"type": "control_datetime",
				#		"answer": {
				#		"month": "04",
				#		"day": "16",
				#		"year": "2024",
				#		"datetime": "2024-04-16 00:00:00"
				#		},
				#		"prettyFormat": "04-16-2024-2024-04-16 00:00:00"
				#	 },
				#	 "4": {
				#		"order": "4",
				#		"text": "Type a question",
				#		"type": "control_email",
				#		"answer": "araariadem0@gmail.com"
				#	 }
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
			'welcome_page': welcome_page,
			'referral_id': form.user.referral_id if hasattr(form, 'user') else None
		}
		return form_data, True
