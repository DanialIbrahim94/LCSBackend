from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.conf import settings
from administrator.models import Coupons


def request_coupons_recharge(user):
	try:
		subject = 'Data Capture Pros - You\'re Running Low On Your Coupon Balance.'
		text_content = f'''
Hi {user.fullName},
You’re running low on your coupon balance! We’d hate for you to run out of coupons when your customer expects one. Please login to your dashboard to recharge your coupon inventory. Your coupons will be generated within 2 minutes.

Step 1: Log into your dashboard. You’ll see a popup prompting you to recharge your inventory.

Step 2: Select your desired quantity, and you will be redirected to our site to complete the purchase.

Step 3: Fill out your payment details, the quantity will already be preselected and check out.

Regards,
Team Data Capture Pros
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
Team Data Capture Pros
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


def send_coupon_email(sendBy_id, sendTo_email, coupon_code):
    subject = 'Congratulations On Receiving A Free $100 Coupon Code!'
    text_content = f'''
Congrats!

Here Is A Unique Coupon Code To Access Up To $100 In GUARANTEED Travel Savings BELOW Prices On 1 Million Worldwide Hotels And Thousands Of 5-Star Resorts Listed On Expedia, Priceline, And Others.
Coupon Code: {coupon_code}
Follow the steps below to redeem your coupon code:
Step 1: Visit https://mytravelplanet.com and click on “Redeem Code”
Step 2: Follow the Instructions On The Page and Fill Out The Form.
Step 3: Enjoy Your Hotel Savings!
For any questions, feel free to reach out to us at https://mytravelplanet.com/contact
    '''
    html_content = f'''
Congrats!
<br />
<br />
Here Is A Unique Coupon Code To Access Up To $100 In GUARANTEED Travel Savings BELOW Prices On 1 Million Worldwide Hotels And Thousands Of 5-Star Resorts Listed On Expedia, Priceline, And Others.
<br />
<br />
<span style="font-size: 17px;color: red;">Coupon Code: <b style="color: blue;">{coupon_code}</b></span>
<p>
Follow the steps below to redeem your coupon code:
<br />
<b>Step 1:</b> Visit https://mytravelplanet.com and click on “Redeem Code”
<br />
<b>Step 2:</b> Follow the Instructions On The Page and Fill Out The Form.
<br />
<b>Step 3:</b> Enjoy Your Hotel Savings!
</p>
For any questions, feel free to reach out to us at https://mytravelplanet.com/contact
    '''
    msg = EmailMultiAlternatives(subject,text_content,from_email=settings.EMAIL_HOST_USER,to=[sendTo_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
