from woocommerce import API

from django.conf import settings

from administrator.models import User, Coupons, CompletedOrders


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

	def get(self, request, params={}, paginator=False):
		if paginator:
			response = []
			page = 1
			params['per_page'] = 100

			while True:
				print(str(page) + ' | ' + str(len(response)))
				params['page'] = page
				temp = self.api.get(request, params=params).json()
				if not temp:
					break
				response += temp
				page += 1
			return response
		else:
			return self.api.get(request, params=params)

	def post(self, request, data, params={}):
		response = self.api.post(request, data, params=params)
		return response

	def get_orders(self, email):
		completed_orders_qs = CompletedOrders.objects.all().values_list('order_id', flat=True)
		response = self.get('orders', paginator=True)
		filtered_orders = []
		while response:
			order = response.pop(0)
			if order and order['billing']['email'] == email and order.get('id', '') not in completed_orders_qs:
				filtered_orders.append(order)

		return filtered_orders

	def get_customer(self, user):
		email = user.email
		customer = None
		customers = self.get('customers', paginator=True)

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
		}
		customer = self.get_customer(user)
		if customer and customer.get('id'):
			data["customer_id"] = customer.get('id')
		else:
			data["billing"] = {
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

		response = self.post('orders', data)
		return response

	def verify_order(self, order_id):
		completed_orders_qs = CompletedOrders.objects.filter(order_id=order_id)
		if completed_orders_qs.exists():
			return False, {'message': 'Order already processed!'}

		order = self.get(f'orders/{order_id}')
		if order.ok:
			_order = order.json()
			status = _order['status']
			if status != 'completed':
				return False, {'message': 'The order has not been paid for yet.'}

			user_email = _order['billing']['email']
			wc_variations = settings.WOOCOMMERCE_PRODUCT_VARIATIONS
			amount = list(wc_variations.keys())[list(wc_variations.values()).index(_order['line_items'][0]['variation_id'])]

			qs = User.objects.filter(email=user_email)
			if qs.exists():
				user = qs.first()
				bulk_coupons = Coupons.objects.filter(used=False)
				if bulk_coupons.count() < amount:
					return False, {'message': 'All coupons have been claimed. Please contact the administrators.'}

				coupons_ids = bulk_coupons.values_list('pk', flat=True)[:amount]
				Coupons.objects.filter(pk__in=coupons_ids).update(used=True, user=user)

				CompletedOrders(order_id=order_id).save()
				return True, {'is_valid': True}
			else:
				pass

		return False
