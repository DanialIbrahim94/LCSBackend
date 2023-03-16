from django.utils import timezone

from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from administrator.models import Coupons
from administrator.options import request_coupons_recharge


@receiver([post_save, post_delete], sender=Coupons)
def check_coupons_threshold(sender, instance, **kwargs):
	user = instance.user
	if not user: # bulk coupon
		return
	if not user.role or user.role.id != 3:
		return
	quantity = instance.get_quantity()
	
	if quantity < settings.MINIMUM_COUPONS_AMOUNT:
		last_recharge = user.get_last_recharge_request_in_days()

		if last_recharge == -1 or last_recharge >= settings.SEND_RECHARGE_REQUEST_COOLDOWN:
			succeeded = request_coupons_recharge(user)

			if succeeded:
				user.last_recharge_request = timezone.now()
				user.save()
