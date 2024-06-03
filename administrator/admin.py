import csv

from django import forms
from django.db import transaction
from django.contrib import admin
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model

from administrator.models import Coupons, User, Role, Business


class CustomFooForm(forms.ModelForm):
	bulk_coupons = forms.FileField(
		label='Upload your file',
		help_text='Upload bulk of coupons.',
		validators=[FileExtensionValidator(allowed_extensions=['csv'])]
	)

	class Meta:
		model = Coupons
		fields = []

	def save(self, commit=True):
		# Call the superclass's save method to create the model instance
		instance = super().save(commit=False)
		user = User.objects.first()
		# Add custom logic here to modify the instance as needed
		bulk_coupons = self.cleaned_data['bulk_coupons']  # Example
		reader = csv.reader(bulk_coupons.read().decode('utf-8').splitlines())
		coupon_codes = [row[0] for row in reader]

		# Create a Coupons instance for the first coupon code
		first_coupon_code = coupon_codes.pop(0)
		instance = Coupons(code=first_coupon_code, user=user)

		# Create Coupons instances for the remaining coupon codes
		created_coupons = []
		for coupon_code in coupon_codes:
			created_coupons.append(Coupons(code=coupon_code, user=user))

		# Bulk create all Coupons instances
		with transaction.atomic():
			Coupons.objects.bulk_create([instance] + created_coupons)

		return instance


@admin.register(Coupons)
class CouponsAdmin(admin.ModelAdmin):
	list_display = ('code', 'user')
	form = CustomFooForm

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		user = User.objects.first()
		return qs.filter(user=user)


class RoleAdmin(admin.ModelAdmin):
    list_display = ('roleType',)


class BusinessAdmin(admin.ModelAdmin):
    list_display = ('businessType',)


class UserAdmin(admin.ModelAdmin):
    list_display = ('fullName', 'email', 'phone', 'role', 'couponCount')
    list_filter = ('role', 'business', 'createdAt', 'updatedAt')
    search_fields = ('fullName', 'email', 'phone', 'address', 'jotform_id')
    exclude = ('birthday', 'couponCount', 'jotform_id', 'leads_count', 'createdAt', 'updatedAt', 'get_last_recharge_request_in_days', 'last_recharge_request')

admin.site.register(Role, RoleAdmin)
admin.site.register(Business, BusinessAdmin)
admin.site.register(User, UserAdmin)
