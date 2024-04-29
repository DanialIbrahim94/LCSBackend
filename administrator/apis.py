import json
import time

import requests
from woocommerce import API
from jotform import JotformAPIClient

from django.conf import settings

from administrator.models import User, Coupons
from administrator.countries import countries_list


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

		return response.json()['content']['welcomePage'][0]

	def create_form(self, name, elements, welcome, verification_code, form_type='card'):
		questions = {
			"1": {
				"type": "control_head",
				"text": "<b style='color: #4a98d2;'>The $100</b> Hotel Saver Gift",
				"subHeader": """You’re about to receive a $100 coupon that you can redeem and use at 1,000,000 worldwide hotels and resorts up to 2-years, once redeemed. There is nothing to join, no blackout dates, no travel restrictions, and no timeshare presentations to attend.
					<b>NO GIMMICKS, JUST SAVINGS</b>
      				<small>You will be emailed with instructions how to use this within 5-minutes once submitted</small>""",
				"order":"1",
				"showQuestionCount": "No",
				"headerType": ['large', 'small'],
				"name":"Header"
			}
		}
		index = 2

		for value in elements:
			if value.get('required'):
				value['required'] = 'Yes' if value['required'] else 'No'

			if value.get('type') == 'control_email':
				value['verificationCode'] = 'Yes' if verification_code else 'No'

			if value.get('type') == 'control_address':
				# Country
				required = value.get('required', 'No')
				countries = countries_list.values()
				print(countries)

				value['type'] = 'control_dropdown'
				value['options'] = '|'.join(countries)
				value['required'] = required

				questions[str(index)] = value
				index += 1
				# State, City
				value = {
					'type': 'control_textbox',
					'text': 'State, City',
					'required': required
				}
				questions[str(index)] = value

			questions[str(index)] = value
			index += 1

		questions[str(index)] = {
			'type': 'control_checkbox',
			'text': 'required',
			'options': 'I understand that by accepting this $100 hotel saver gift, my information may be sold for marketing purposes!',
			'required': 'Yes',
		}
		index += 1

		questions[str(index)] = {
			'type': 'control_button',
			'text': 'Get Yours Now!',
			'buttonStyle': 'simple_blue',
			'required': 'Yes'
		}

		form = {
			'questions': questions,
			'properties': {
				'title': name,
				'theme': form_type,
				'styles': ['baby_blue'],
			},
		}

		print(form)

		# for now, the API will keep trying until the form is finally created
		failed_form_ids = []
		max_retries = 15
		retries = 0
		while retries <= max_retries:
			retries += 1
			try:
				response = self.api.create_form(form)
				# Now make sure that all the questions are saved
				form_id = response['id']
				created_questions = self.api.get_form_questions(form_id)
				print(len(created_questions), len(questions))
				if created_questions and len(created_questions) == len(questions):
					break  # break out of the loop if no exception is raised
				else:
					failed_form_ids.append(form_id)
			except Exception as e:
				# handle the error
				print(f"Error creating form: {e}")
		
		# the form was not created
		if retries > max_retries:
			return None, False
		try:
			for failed_form_id in failed_form_ids:
				res = self.api.delete_form(failed_form_id)
				print(res)
		except Exception as e:
			print('Error', e)

		# self.update_form_properties(form_id, settings.JOTFORM_API_KEY, welcome)

		# Change form type to the modern type: Card form
		# form_id = response['id']
		# properties = json.dumps({
		# 	'properties': {
		# 		'formType': 'cardForm'
		# 	}
		# })
		# r = self.api.set_multiple_form_properties(form_id, properties)

		return response, True

	def update_form(self, name, elements, form_id):
		# build the questions dictionary
		questions = {}
		for i, element in enumerate(elements):
			print(element)
			questions[str(i+1)] = {
				"type": element["type"],
				"text": element["text"],
				"required": "Yes" if element.get("required") else "No",
				# "name": f"Header{i+1}"
			}

		# build the data to send in the PUT request
		headers = {"Content-Type": "application/json"}
		for qid, question in questions.items():
			url = f"https://api.jotform.com/form/{form_id}/question/{qid}?apiKey={settings.JOTFORM_API_KEY}"

			# send the PUT request
			response = requests.post(url, data=json.dumps(question), headers=headers)
			print(response)
			print(response.json())

		if response.ok:
			return response.json(), True
		else:
			return None, False

	def get_submissions(self, form_id):
		try:
			response = self.api.get_form_submissions(form_id)
			for submission in response:
				answers = submission.get('answers', {})
				if '1' in answers:  # Assuming '1' is the control_header question ID
					del answers['1']
			return response, True
		except Exception as e:
			print(e)
			return None, False

	def get_form_data(self, form_id):
		form = self.api.get_form(form_id)
		welcome_page = self.get_form_welcome_page(form_id)
		form_questions = self.api.get_form_questions(form_id)
		print(form_questions)
		form_data = {
			'id': form_id,
			'name': form['title'],
			'questions': form_questions,
			'welcome_page': welcome_page
		}
		return form_data, True
