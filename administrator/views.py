import os
import csv
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.http import HttpResponse

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .models import User, Role, Business, Coupons, CouponHistory, DownHistory
from .serializers import *
from .apis import LeadsOrderAPI, WooCommerceAPI, JotformAPI


@api_view(['POST'])
def auth_login(request):
    if request.method == 'POST':
        data = None
        try:
            data_qs = User.objects.filter(email__icontains=request.data.get('email').lower())
            if data_qs.exists():
                data = data_qs.first()
            else:
                Response(status=status.HTTP_400_BAD_REQUEST, data="This email doesn' t exist.")
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data="This email doesn' t exist.")
        serializer = UserSerializer(data, context={'request': request})

        if request.data.get('password') == serializer.data.get('password'):
            return Response({'data': serializer.data})

        return Response(status=status.HTTP_400_BAD_REQUEST, data="Password isn' t correctly.")


@api_view(['POST'])
def auth_signUp(request):
    if request.method == 'POST':
        if User.objects.filter(email=request.data.get('email')).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data="This email already exists.")
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST, data="Bad request.")


@api_view(['POST'])
def user_add(request):
    print('doing this now')
    if request.method == 'POST':
        if User.objects.filter(email=request.data.get('email')).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            sendTo_email = request.data.get("email")
            print(request.data)
            if sendTo_email:
                sendTo_fullName = request.data.get("fullName")
                sendTo_password = request.data.get("password")
                print(sendTo_email, sendTo_password)

                subject = 'Data Capture Pros - Account has been created on DCP’s Lead Capture System.'
                text_content = f'''
Hi {sendTo_fullName},

Your account has been created on DCP’s Lead Capture System. To begin capturing customer data and distributing hotel saving plans, please log into your private dashboard using the credentials mentioned below:

Login URL: https://getcustomerdata.com
Username: {sendTo_email}
Password: {sendTo_password}

If you haven’t been assigned any saving plans yet, please send an email at support@datacapturepros.com and we will get back to you as soon as possible.

Regards,
Team DCP
                '''
                html_content = f'''
Hi {sendTo_fullName},
<p>
Your account has been created on DCP’s Lead Capture System. To begin capturing customer data and distributing hotel saving plans, please log into your private dashboard using the credentials mentioned below:
<br />
<b>Login URL:</b> <a href="https://getcustomerdata.com">https://getcustomerdata.com</a>
<br />
<b>Username:</b> {sendTo_email}
<br />
<b>Password:</b> {sendTo_password}
</p>
Regards,<br />
Team Data Capture Pros
                '''
                print(text_content)
                recipient_list = [sendTo_email]
                msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, recipient_list)
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            return Response(status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET', 'POST'])
def users_list(request):
    if request.method == 'GET':
        users = User.objects.select_related().all().order_by('business')
        serializer = UserSerializer(users, context={'request': request} ,many=True)
        return Response({'data': serializer.data})
    
    elif request.method == 'POST':
        fullName = request.data.get('fullName')
        email = request.data.get('email')
        address = request.data.get('address')
        business_id = request.data.get('business')
        role_id = request.data.get('role')
        users = User.objects.select_related().all().order_by('business')
        if fullName:
            users = users.filter(fullName=fullName)
        if email:
            users = users.filter(email=email)
        if address:
            users = users.filter(address=address)
        if business_id:
            users = users.filter(business_id=business_id)
        if role_id:
            users = users.filter(role_id__gte=role_id)
        
        serializer = UserSerializer(users, context={'request': request}, many=True)
        return Response({'data': serializer.data})
    

@api_view(['POST'])
def users_download_select(request):
    if request.method == 'POST':
        from_user_id = request.data.get('from_user')
        business = request.data.get('business')
        downCount = request.data.get('downCount')
        role = request.data.get('role')
        downUsers = User.objects.all()
        if business:
            downUsers = downUsers.filter(business_id = business)
        if role:
            if role == 3:
                downUsers = downUsers.filter(role_id__gt=role)
            else:
                downUsers = downUsers.filter(role_id__gte=role)
        data = []
        index = 0
        for i in downUsers:
            if index < downCount:
                if not DownHistory.objects.filter(from_user=from_user_id, down_user=i.id).exists():
                    data.append(i)
                    index = index + 1
        serializer = UserSerializer(data, context={'request': request} ,many=True)
        return Response({'data': serializer.data})
    

@api_view(['POST'])
def users_download_save(request):
    if request.method == 'POST':
        from_user= request.data.get('from_user')
        downUsers = request.data.get('downUsers')
        for i in downUsers:
            downhistory = DownHistory.objects.create(from_user=from_user, down_user=i)
            histrySerializer = DownHistorySerializer(data=downhistory)
            if histrySerializer.is_valid():
                histrySerializer.save()
        return Response(status=status.HTTP_201_CREATED)

    
@api_view(['POST'])
def users_downloadCount(request):
    if request.method == "POST":
        from_user_id = request.data.get('from_user')
        role = request.data.get('role')
        business = request.data.get('business')
        downUsers = User.objects.all()
        if business:
            downUsers = downUsers.filter(business_id = business)
        if role:
            if role == 3:
                downUsers = downUsers.filter(role_id__gt=role)
            else:
                downUsers = downUsers.filter(role_id__gte=role)
        count = 0
        for i in downUsers:
            if not DownHistory.objects.filter(from_user=from_user_id).filter(down_user=i.id).exists():
                count = count + 1
        return Response({'downableCount': count})
                

@api_view(['GET', 'PUT', 'DELETE'])
def users_detail(request, id):
    try:
        data = User.objects.get(id=id)

    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserSerializer(data, context={'request': request})
        return Response(serializer.data)

    if request.method == 'PUT':
        User.objects.filter(id=id).update(role=request.data.get("role"))
        data = User.objects.get(id = id)
        serializer = UserSerializer(data, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'DELETE':
        data.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

@api_view(['GET', 'POST'])
def roles_list(request):
    if request.method == 'GET':
        roles = Role.objects.all()
        serializer = RoleSerializer(roles,context={'request': request} ,many=True)
        return Response({'data': serializer.data })
        
    elif request.method == 'POST':
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            roles = Role.objects.all()
            serializer = RoleSerializer(roles, context={'request': request}, many=True)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['PUT', 'DELETE'])
def roles_edit(request, id):
    try:
        data = Role.objects.get(id=id)
    except Role.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'PUT':
        serializer = RoleSerializer(data, data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        data.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

@api_view(['GET', 'POST'])
def businesses_list(request):
    if request.method == 'GET':
        businesses = Business.objects.all().order_by('id')
        serializer = BusinessSerializer(businesses,context={'request': request} ,many=True)
        return Response({'data': serializer.data})

    elif request.method == 'POST':
        serializer = BusinessSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            businesses = Business.objects.all()
            serializer = BusinessSerializer(businesses,context={'request': request} ,many=True)
            return Response({'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['PUT', 'DELETE'])
def businesses_edit(request, id):
    try:
        data = Business.objects.get(id=id)
    except Business.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'PUT':
        Business.objects.filter(id=id).update(businessType = request.data.get("businessType"))
        businesses = Business.objects.all().order_by('id')
        serializer = BusinessSerializer(businesses, context={'request': request} ,many=True)
        return Response({'data': serializer.data})

    elif request.method == 'DELETE':
        data.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def coupon_add(request, id):
    if request.method == 'POST':
        same_code = 0
        success_code = 0
        for code in request.data:
            try:
                serializer = CouponSerializer(data=code)
                if serializer.is_valid():
                    serializer.save()
                    success_code = success_code + 1
                else:
                    raise IntegrityError('Not valid')
            except IntegrityError as e:
                print(e)
                same_code = same_code + 1

        data = Coupons.objects.all().filter(user_id=id)
        codeSerializer = CouponSerializer(data, context={'request': request}, many=True)
        return Response({'data': codeSerializer.data, 'same_code': same_code, "success_code": success_code})
    

@api_view(['GET', 'POST'])
def coupons_list(request, id):
    if request.method == 'GET':
        data = Coupons.objects.all().filter(user_id=id)
        serializer = CouponSerializer(data,context={'request': request} ,many=True)
        return Response({'data': serializer.data})
    if request.method == 'POST':
        count = request.data.get('count')
        couponSome = Coupons.objects.filter(user_id = id)[:count]
        serializer = CouponSerializer(couponSome,context={'request': request} ,many=True)
        return Response({'data': serializer.data})
    

@api_view(['GET'])
def coupons_count(request, id):
    if request.method == 'GET':
        count = Coupons.objects.all().filter(user_id=id).count()
        return Response({'count': count})
    

@api_view(['POST'])
def coupons_sendToBsUser(request):
    if request.method == 'POST':
        sendTo_id = request.data.get("sendTo_id")
        sendTo_email = request.data.get("sendTo_email")
        sendBy_id = request.data.get("sendBy_id")
        sendBy_email = request.data.get("sendBy_email")
        sendCount = int(request.data.get("sendCount"))
        user_qs = User.objects.filter(id=sendTo_id)
        if user_qs.exists():
            for send_coupon in Coupons.objects.filter(user_id = sendBy_id)[:sendCount]:
                send_coupon.user = user_qs.first()
                send_coupon.save()
        else:
            return Response({'message': 'Can\'t send coupon(s) to user'}, status=serializer.HTTP_400_BAD_REQUEST)

        data = Coupons.objects.filter(user_id = sendBy_id)
        serializer = CouponSerializer(data,context={'request': request} ,many=True)

        subject = 'Data Capture Pros - You\'ve Just Been Assigned Coupon Codes!'
        text_content = f'''
Hi {user_qs.first().fullName},
You’ve just been assigned {sendCount} Coupon codes!
Feel free to reach out to us if you have any questions at https://datacapturepros.com/contact
Regards,
Team Data Capture Pros
        '''
        html_content = f'''
Hi {user_qs.first().fullName},
<p>
You’ve just been assigned {sendCount} Coupon codes!
<br />
Feel free to reach out to us if you have any questions at https://datacapturepros.com/contact
</p>
Regards,<br />
Team Data Capture Pros
        '''
        email_from = sendBy_email
        recipient_list = [sendTo_email]
        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        history_serializer = CouponHistorySerializer(data=request.data.get("history"))
        if history_serializer.is_valid():
            history_serializer.save()
        return Response({'data': serializer.data})


@api_view(['GET'])
def coupons_history(request):
    if request.method == 'GET':
        coupons = CouponHistory.objects.all()
        serializer = CouponHistorySerializer(coupons,context={'request': request} ,many=True)
        return Response({'data': serializer.data})
    

@api_view(['POST'])
def send_message(request):
    if request.method == 'POST':
        subject = request.data.get("subject")
        message = request.data.get("message")
        from_email = request.data.get("from_email")
        recipient_list = request.data.get("recipient_list")
        if from_email and recipient_list:
            try: 
                send_mail(subject=subject, message=message, from_email=settings.EMAIL_HOST_USER, recipient_list=recipient_list)
            except BadHeaderError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST'])
def coupons_sendToCustomer(request):
    if request.method == 'POST':
        sendBy_id = request.data.get("sendBy_id")
        sendTo_email = request.data.get("sendTo_email")
        sendBy_email = request.data.get("sendBy_email")
        send_code = request.data.get("send_code")

        send_coupon_email(sendBy_id, sendTo_email, send_code)
        Coupons.objects.get(code=send_code, user_id=sendBy_id).delete()

        history_serializer = CouponHistorySerializer(data=request.data.get("history"))
        if history_serializer.is_valid():
            history_serializer.save()
        return Response(status=status.HTTP_201_CREATED)


@api_view(['POST'])
def request_coupons(request):
    user_id = request.data.get('user_id')
    user = None
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(data={'message': "You don't have permission!"}, status=status.HTTP_400_BAD_REQUEST)

    amount = request.data.get('amount')
    if amount < 1:
        return Response(data={'message': "Amount of coupons to be created must be valid!"}, status=status.HTTP_400_BAD_REQUEST)

    api = WooCommerceAPI()

    # Place an order
    order = api.order(user, amount)
    if order.ok:
        # TODO: save order to DB until it is completed!

        # Return the payment link
        data = {
            'payment_url': order.json()['payment_url']
        }

        return Response(data=data, status=status.HTTP_200_OK)

    return Response(data={'message': order.reason}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_orders(request, user_id):
    user = None
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(data={'message': "You don't have permission!"}, status=status.HTTP_400_BAD_REQUEST)

    api = WooCommerceAPI()

    # Place an order
    orders = api.get_orders(user.email)
    data = {
        'data': orders
    }

    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET'])
def verify_order(request, order_id):
    api = WooCommerceAPI()

    # Verify the order
    is_completed, data = api.verify_order(order_id)
    if is_completed:
        # release the coupons

        return Response(data=data, status=status.HTTP_200_OK)

    return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_jotform(request):
    print(request.data)
    user_id = request.data.get('user_id')
    user = None
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(data={'message': "Hey, you don't have permission to do that!"}, status=status.HTTP_400_BAD_REQUEST)

    if user.jotform_id:
        return Response(
            data={
                'message': "Sorry, you have already created a form. You can only create one form per account."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    api = JotformAPI()
    data = request.data
    name = data['formName']
    elements = data['formElements']
    welcome = data['welcomePage']
    verification_code = data['verificationCode']

    response, ok = api.create_form(name, elements, welcome, verification_code)

    if ok:
        form_id = response['id']
        form_url = response['url']
        user.jotform_id = form_id
        user.save()

        res_data = {
            'message': 'Form created successfully!',
            'form_url': form_url,
            'form_id': form_id,
        }
        return Response(res_data, status=status.HTTP_201_CREATED)

    return Response({'message': "Failed to create the form!"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def update_jotform(request, user_id):
    user = None
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(data={'message': "Hey, you don't have permission to do that!"}, status=status.HTTP_400_BAD_REQUEST)

    if not user.jotform_id:
        return Response(
            data={
                'message': "Sorry, You should create a form first."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    api = JotformAPI()
    data = request.data
    name = data['formName']
    elements = data['formElements']
    response, ok = api.update_form(name, elements, user.jotform_id)

    if ok:
        res_data = {
            'message': 'Form updated successfully!'
        }
        return Response(res_data, status=status.HTTP_200_OK)

    return Response({'message': "Failed to update the form!"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_jotform(request, user_id):
    user = None
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(data={'message': "Hey, you don't have permission to do that!"}, status=status.HTTP_400_BAD_REQUEST)

    if not user.jotform_id:
        return Response(
            data={
                'message': "Sorry, You should create a form first."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    api = JotformAPI()
    response, ok = api.get_form_data(user.jotform_id)

    if ok:
        return Response({'form': response}, status=status.HTTP_200_OK)

    return Response({'message': 'Form not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_submissions(request, user_id):
    user = None
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(data={'message': "Hey, you don't have permission to do that!"}, status=status.HTTP_400_BAD_REQUEST)

    form_id = user.jotform_id
    api = JotformAPI()

    submissions, ok = api.get_submissions(form_id)

    if ok:
        leads_count = len(submissions)
        total_leads_count = len(submissions)
        filtered_submissions = submissions[:leads_count]

        for submission in submissions[leads_count:]:
            filtered_submission = {**submission}
            filtered_answers = {}

            for answer_key, answer_value in filtered_submission['answers'].items():
                filtered_answers[answer_key] = {**answer_value}
                
                if answer_value['type'] == 'control_fullname':
                    first_name = answer_value.get('answer', {}).get('first', '')
                    last_name = answer_value.get('answer', {}).get('last', '')
                    last_name_stars = '*' * len(last_name)

                    filtered_answers[answer_key]['answer'] = {'first': first_name, 'last': 'Hidden'}
                    filtered_answers[answer_key]['prettyFormat'] = first_name + ' ' + last_name_stars
                else:
                    filtered_answers[answer_key]['answer'] = 'Hidden'  # Replace the answer value with a placeholder text

            filtered_submission['answers'] = filtered_answers
            filtered_submissions.append(filtered_submission)

        data = {
            'submissions': filtered_submissions,
            'leads_count': leads_count,
            'total_leads_count': total_leads_count,
        }
        return Response(data, status=status.HTTP_200_OK)

    return Response({'message': "Failed retrieve submissions!"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def download_submissions(request, user_id):
    user = None
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(data={'message': "Hey, you don't have permission to do that!"}, status=status.HTTP_400_BAD_REQUEST)

    form_id = user.jotform_id
    api = JotformAPI()

    submissions, ok = api.get_submissions(form_id)
    leads_count = len(submissions)

    if ok:
        # Define the output file name
        filename = 'submissions.csv'

        # Extract the header row from the first submissions item
        header = list(submissions[0]['answers'].values())
        header = [item['text'] for item in header]

        # Extract the submissions rows from all submissions items
        rows = []
        for item in submissions:
            row = list(item['answers'].values())
            row = [item.get('answer', '') for item in row]
            rows.append(row)

        # Create a CSV response object with appropriate headers
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Write the submissions to the response
        writer = csv.writer(response)
        writer.writerow(header)
        writer.writerows(rows)

        return response

    return Response({'message': "Failed retrieve submissions!"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def order_leads(request):
    user_id = request.data.get('user_id')
    user = None
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(data={'message': "You don't have permission!"}, status=status.HTTP_400_BAD_REQUEST)

    quantity = request.data.get('quantity')
    if quantity < 1:
        return Response(data={'message': "Amount of coupons to be created must be valid!"}, status=status.HTTP_400_BAD_REQUEST)

    api = LeadsOrderAPI()

    # Place an order
    order = api.order_leads(user, quantity)
    print(order.json())
    if order.ok:
        # Return the payment link
        data = {
            'payment_url': order.json()['payment_url']
        }

        return Response(data=data, status=status.HTTP_200_OK)

    return Response(data={'message': order.reason}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_lead_orders(request, user_id):
    user = None
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(data={'message': "You don't have permission!"}, status=status.HTTP_400_BAD_REQUEST)

    api = LeadsOrderAPI()

    # Place an order
    orders = api.get_orders(user.email)
    data = {
        'data': orders
    }

    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET'])
def verify_lead_order(request, order_id):
    api = LeadsOrderAPI()

    # Verify the order
    is_completed, data = api.verify_order(order_id)
    if is_completed:
        # release the coupons

        return Response(data=data, status=status.HTTP_200_OK)

    return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    
