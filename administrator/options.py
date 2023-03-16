from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.conf import settings


def request_coupons_recharge(user):
	try:
		subject = 'Data Capture Pro - You\'re Running Low On Your Coupon Balance.'
		text_content = f'''
Hi {user.fullName},
You’re running low on your coupon balance! We’d hate for you to run out of coupons when your customer expects one. Please login to your dashboard to recharge your coupon inventory. Your coupons will be generated within 2 minutes.

Step 1: Log into your dashboard. You’ll see a popup prompting you to recharge your inventory.

Step 2: Select your desired quantity, and you will be redirected to our site to complete the purchase.

Step 3: Fill out your payment details, the quantity will already be preselected and check out.

Regards,
Team Data Capture Pro
		'''
		html_content = f'''
Hi {user.fullName},
<p>
You’re running low on your coupon balance! We’d hate for you to run out of coupons when your customer expects one. Please login to your dashboard to recharge your coupon inventory. Your coupons will be generated within 2 minutes.
</p>
<b>Step 1:</b> Log into your dashboard. You’ll see a popup prompting you to recharge your inventory.
<br />
<b>Step 2:</b> Select your desired quantity, and you will be redirected to our site to complete the purchase.
<br />
<b>Step 3:</b> Fill out your payment details, the quantity will already be preselected and check out.

<p>
Regards,<br />
Team Data Capture Pro
</p>
		'''
		sender = settings.EMAIL_HOST_USER
		receiver = user.email
		msg = EmailMultiAlternatives(subject, text_content, sender, [receiver])
		msg.attach_alternative(html_content, "text/html")
		msg.send()
	except Exception as e:
		print(e)
		return False
	return True