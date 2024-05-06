import csv

from django import forms
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
		created_coupons = []
		for index, row in enumerate(reader):
			coupon_code = row[0]
			if index == 0:
				instance = Coupons(code=coupon_code, user=user)
				continue

			# Create a Coupons instance for each row in the file
			coupon, created = Coupons.objects.get_or_create(code=coupon_code)
			if created:
				coupon.user = user
				coupon.save()
			created_coupons.append(coupon)

		return created_coupons[0]


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
    list_display = ('fullName', 'email', 'phone', 'address', 'birthday', 'couponCount', 'createdAt', 'updatedAt', 'role', 'business', 'jotform_id', 'leads_count', 'last_recharge_request', 'get_last_recharge_request_in_days')
    list_filter = ('role', 'business', 'createdAt', 'updatedAt')
    search_fields = ('fullName', 'email', 'phone', 'address', 'jotform_id')
    readonly_fields = ('createdAt', 'updatedAt', 'get_last_recharge_request_in_days')

admin.site.register(Role, RoleAdmin)
admin.site.register(Business, BusinessAdmin)
admin.site.register(User, UserAdmin)