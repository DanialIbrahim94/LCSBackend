from django.core.mail import send_mail
from django.conf import settings


def request_coupons_recharge(user):
	try:
		subject = 'Coupons Recharge Request'
		content = 'Please recharge you account, you running low on coupons. Login to your dashboard to get more..'
		sender = settings.EMAIL_HOST_USER
		receiver = user.email
		send_mail(subject, content, sender, [receiver])
	except Exception as e:
		print(e)
		return False
	return True