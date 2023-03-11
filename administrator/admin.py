import csv

from django import forms
from django.contrib import admin
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model

from administrator.models import Coupons


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

		# Add custom logic here to modify the instance as needed
		bulk_coupons = self.cleaned_data['bulk_coupons']  # Example
		reader = csv.reader(bulk_coupons.read().decode('utf-8').splitlines())

		for index, row in enumerate(reader):
			coupon_code = row[0]
			if index == 0:
				instance = Coupons(code=coupon_code, used=False)
				continue

			# Create a Coupons instance for each row in the file
			coupon = Coupons(code=coupon_code, used=False)
			coupon.save()

		return instance


@admin.register(Coupons)
class CouponsAdmin(admin.ModelAdmin):
	list_display = ('code', )
	form = CustomFooForm

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.filter(used=False)