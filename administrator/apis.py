from woocommerce import API

from django.conf import settings


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

	def batch(self, data, params={}):
		response = self.api.post('coupons/batch', data, params=params).json()
		return response

	def post(self, data, params={}):
		response = self.api.post('coupons/', data, params=params).json()
		return response

	def get(self, id, params={}):
		response = self.api.get(f'coupons/{id}', params=params).json()
		return response

	def get_all(self, params={}):
		response = self.api.get('coupons', params=params).json()
		return response

	def put(self, id, data, params={}):
		response = self.api.put(f'coupons/{id}', data, params=params).json()
		return response

	def delete(self, id, params={}):
		response = self.api.delete(f'coupons/{id}', params=params).json()
		return response