import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseNotFound
from rest_framework import viewsets

from .models import Form, Field, Submission
from .serializers import FormSerializer, FieldSerializer, SubmissionSerializer
from .forms import DynamicForm
from administrator.apis import WooCommerceAPI


class FormViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Form.objects.all()
    serializer_class = FormSerializer


class FieldViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FieldSerializer

    def get_queryset(self):
        form_id = self.kwargs['form_id']
        return Field.objects.filter(form_id=form_id)

    def perform_create(self, serializer):
        form_id = self.kwargs['form_id']
        serializer.save(form_id=form_id)


class SubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer


def submit_form(request, slug):
    form = get_object_or_404(Form, slug=slug)
    error_msg = ''

    if request.method == 'POST':
        form_data = DynamicForm(request.POST, fields=form.fields.all())
        if form_data.is_valid():
            submission_data = form_data.cleaned_data
            # Convert datetime fields to strings
            for field_name, field_value in submission_data.items():
                if isinstance(field_value, datetime.date):
                    submission_data[field_name] = field_value.strftime('%Y-%m-%d')
            submission = Submission.objects.create(form=form, data=submission_data)
            if form.verify_email:
                # send verification code
                submission.send_verification_email()
                return redirect(reverse('verify_email', kwargs={'submission_id': submission.id}))
            else:
                api = WooCommerceAPI()
                response = api.redeem_coupon(submission)
                print(response)
                if response.get('success'):
                    return redirect(response.get('redirect_url', '.'))
                else:
                    error_msg = response.get('error', 'Failed to create order, please try again later or contact us for additional support!')
    else:
        form_data = DynamicForm(fields=form.fields.all())

    additional_data = {
        'submit_text': form.submit_text,
        'error_msg': error_msg
    }

    return render(
        request,
        'forms/submit_form.html',
        {'form': form, 'form_data': form_data, 'additional_data': additional_data}
    )


def verify_email(request, submission_id):
    try:
        submission = Submission.all_objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return HttpResponseNotFound('Submission not found')
    
    if submission.form.verify_email:
        if submission.is_verified == True:
            return redirect('success')

        if request.method == 'POST':
            verification_code = request.POST.get('verification_code')
            if verification_code == submission.verification_code:
                submission.is_verified = True
                submission.verification_code = None
                submission.save()
                api = WooCommerceAPI()
                response = api.redeem_coupon(submission)
                if response.get('success'):
                    return redirect(response.get('redirect_url', '.'))
                else:
                    pass
            else:
                return render(request, 'forms/email_verification.html', {'error': 'Invalid verification code'})
        else:
            return render(request, 'forms/email_verification.html')
    else:
        return HttpResponseBadRequest('Email verification is not enabled for this form')


def success(request):
    return render(request, 'forms/success.html')

