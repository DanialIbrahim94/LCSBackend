import uuid
import random
import string

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from email.utils import make_msgid
from administrator.models import Coupons, User
from administrator.options import send_coupon_email


class Form(models.Model):
	agreed_text = 'I understand that by accepting this $100 hotel saver gift, my information may be sold for marketing purposes!'
	submit_text = 'Get Yours Now!'

	name = models.CharField(max_length=250)
	description = models.TextField()
	user = models.ForeignKey('administrator.User', related_name='forms', on_delete=models.CASCADE)
	slug = models.SlugField(unique=True, default=uuid.uuid4)
	verify_email = models.BooleanField(default=False)

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('submission-form', kwargs={'slug': self.slug})


class Field(models.Model):
	TEXT_INPUT = 'control_input'
	EMAIL_INPUT = 'control_email'
	PHONE_INPUT = 'control_phone'
	DATE_INPUT = 'control_date'
	COUNTRY_INPUT = 'control_dropdown'
	IDENTIFIER_CHOICES = (
		(TEXT_INPUT, 'text input'),
		(EMAIL_INPUT, 'email input'),
		(PHONE_INPUT, 'phone input'),
		(DATE_INPUT, 'date input'),
		(COUNTRY_INPUT, 'dropdown input'),
	)

	form = models.ForeignKey('forms.Form', related_name='fields', on_delete=models.CASCADE)
	identifier = models.CharField(max_length=20, choices=IDENTIFIER_CHOICES)
	label = models.CharField(max_length=100)
	options = models.TextField(blank=True, null=True)
	required = models.BooleanField(default=False)
	position = models.SmallIntegerField(default=0)

	def __str__(self):
		return f'{self.form.id}\'s field'


class SubmissionManager(models.Manager):
    def get_queryset(self):
        # Filter submissions to only include is_verified submissions 
        # if the associated form has verify_email set to True
        return (
        	super().get_queryset().filter(
	            form__verify_email=True,
	            is_verified=True
	        ) | super().get_queryset().filter(
	            form__verify_email=False
	        )
		).order_by('-date')


class Submission(models.Model):
	form = models.ForeignKey('forms.Form', related_name='submissions', on_delete=models.CASCADE)
	data = models.JSONField()
	date = models.DateTimeField(auto_now_add=True)
	verification_code = models.CharField(max_length=6, blank=True, null=True)
	is_verified = models.BooleanField(default=False)

	objects = SubmissionManager()
	all_objects = models.Manager()

	def __str__(self):
		return f'{self.form.id}\'s submission'

	def _generate_verification_code(self):
		return ''.join(random.choices(string.digits, k=6))

	def _get_email(self):
		# Iterate through keys to find email field in a case-insensitive way
		for key in self.data:
			if key.lower() == 'email':
				return self.data[key]

		for field in self.form.fields.all():
			if field.identifier == Field.EMAIL_INPUT:
				return self.data[field.label]

		return None

	def send_verification_email(self):
		if not self.verification_code:
			self.verification_code = self._generate_verification_code()
			self.save()

		subject = 'Email Verification'
		html_message = render_to_string('emails/verification_email.html', {'verification_code': self.verification_code})
		text_message = strip_tags(html_message) # Strip HTML tags for plain text version
		email = self._get_email()

		if not email:
			# Handle missing or invalid email field in data
			return False

		msg = EmailMultiAlternatives(subject, text_message, settings.EMAIL_HOST_USER, [email])
		msg.attach_alternative(html_message, "text/html")
		msg['Message-ID'] = make_msgid()
		msg.send()

	def verify_email_code(self, verification_code):
		if verification_code == self.verification_code:
			self.is_verified = True
			self.save()
			return True
		return False

	def send_coupon(self):
		user = self.form.user
		coupon = Coupons.objects.filter(user=user).first()
		if not coupon:
			admin_user = User.objects.first()
			coupon = Coupons.objects.filter(user=admin_user).first()

		email = self._get_email()
		send_coupon_email(user.id, email, coupon.code)
		coupon.delete()