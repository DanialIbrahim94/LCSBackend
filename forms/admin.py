from django.contrib import admin
from .models import Form, Field, Submission


class FieldInline(admin.TabularInline):
    model = Field
    extra = 1


class FormAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'user')
    inlines = [FieldInline]


class FieldAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'label', 'form')


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('form', 'date')
    readonly_fields = ('data', 'date')


admin.site.register(Form, FormAdmin)
admin.site.register(Field, FieldAdmin)
admin.site.register(Submission, SubmissionAdmin)
