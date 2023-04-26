import json
import time

from woocommerce import API
from jotform import JotformAPIClient

from django.conf import settings

from administrator.models import User, Coupons


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


class JotformAPI():
	api = None
	def __init__(self):
		self.api = JotformAPIClient(settings.JOTFORM_API_KEY)

	def create_form(self, name, elements, form_type='card'):
		questions = {}

		for index, value in enumerate(elements):
			if value.get('required'):
				value['required'] = 'Yes' if value['required'] else 'No'
			questions[str(index+1)] = value

		form = {
			'questions': questions,
			'properties': {
				'title': name,
				'theme': form_type,
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

		# Change form type to the modern type: Card form
		form_id = response['id']
		properties = json.dumps({
			'properties': {
				'formType': 'cardForm'
			}
		})
		r = self.api.set_multiple_form_properties(form_id, properties)

		return response, True

	def update_form(self, name, elements, form_id):
		# get the existing form
		form = self.api.get_form(form_id)
		if not form:
			return None, False
		
		# update the form with the new name and elements
		questions = {}
		for index, value in enumerate(elements):
			if value.get('required'):
				value['required'] = 'Yes' if value['required'] else 'No'
			questions[str(index+1)] = value
		form['questions'] = questions
		form['title'] = name
		
		# update the form
		response = self.api.update_form(form_id, form)
		if not response:
			return None, False
		
		return response, True

	def get_submissions(self, form_id):
		try:
			response = self.api.get_form_submissions(form_id)
			return response, True
		except Exception as e:
			print(e)
			return None, False

	def get_form_data(self, form_id):
		form = self.api.get_form(form_id)
		print(form)
		form_questions = self.api.get_form_questions(form_id)
		print(form_questions)
		form_data = {
			'id': form_id,
			'name': form['title'],
			'questions': form_questions,
		}
		return form_data, True
