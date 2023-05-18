import pytz
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from administrator.apis import LeadsOrderAPI
from administrator.models import User, Coupons
from administrator.options import send_coupon_email


class Command(BaseCommand):
    help = 'Process new lead orders'

    def handle(self, *args, **options):
        # Connect to Jotform API and retrieve all submissions
        api = LeadsOrderAPI()
        # grab only Business Manager users
        bm_users = User.objects.filter(role=2)

        for user in bm_users:
            orders = api.get_orders(user.email)

            for order in orders:
                api.verify_order(order['id'])
