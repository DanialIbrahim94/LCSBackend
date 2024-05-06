from django import forms
from django.core.validators import RegexValidator
from django.forms.widgets import DateTimeInput

from .models import Field


class TelField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.TextInput(attrs={'type': 'tel'}))
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        # You can add any additional validation logic here if needed
        return value


class DynamicForm(forms.Form):
    def __init__(self, *args, fields=None, **kwargs):
        super(DynamicForm, self).__init__(*args, **kwargs)

        if fields:
            for field in fields:
                field_name = field.label
                field_type = field.identifier

                if field_type == Field.TEXT_INPUT:
                    self.fields[field_name] = forms.CharField(
                        required=field.required,
                        label=field_name
                    )
                elif field_type == Field.EMAIL_INPUT:
                    self.fields[field_name] = forms.EmailField(
                        required=field.required,
                        label=field_name
                    )
                elif field_type == Field.PHONE_INPUT:
                    self.fields[field_name] = TelField(
                        required=field.required,
                        label=field_name,
                        max_length=17
                    )
                elif field_type == Field.DATE_INPUT:
                    self.fields[field_name] = forms.DateField(
                        required=field.required,
                        label=field_name,
                        widget=DateTimeInput(attrs={'type': 'datetime-local'})
                    )
                elif field_type == Field.COUNTRY_INPUT:
                    choices = [(choice, choice) for choice in field.options.split('|')]
                    self.fields[field_name] = forms.ChoiceField(
                        choices=choices,
                        required=field.required,
                        label=field_name
                    )

