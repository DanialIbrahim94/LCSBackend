import getpass

from django.core.management.base import BaseCommand, CommandError

from administrator.models import User, Role, Business
from administrator.serializers import RegisterSerializer


class Command(BaseCommand):
    help = 'Create a superuser'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)


    def handle(self, *args, **options):
        fullName = input('Full Name: ')
        email = input('Email: ')
        address = input('Address: ')
        birthday = input('Birthday(YYYY-MM-DD): ')
        phone = input('Phone: ')
        password = None

        while not password:
            password1 = getpass.getpass()
            password2 = getpass.getpass("Password (again): ")
            if password1 != password2:
                self.stderr.write("Error: Your passwords didn't match.")
                # Don't validate passwords that don't match.
                continue
            if password1.strip() == "":
                self.stderr.write("Error: Blank passwords aren't allowed.")
                # Don't validate blank passwords.
                continue
            password = password1
        
        role = Role(roleType='admin')
        role.save()
        business = Business(businessType='admin')
        business.save()
        data = {
            'fullName': fullName,
            'email': email,
            'password': password,
            'address': address,
            'birthday': birthday,
            'phone': phone,
            'role': role.pk,
            'business': business.pk,
            'couponCount': 0
        }
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            print('Account created successfully')

        else:
            errors_formatted = ', '.join(map(lambda s: s.capitalize(), list(serializer.errors)))
            print('Please re-enter correctly the value(s) of the following variable(s):', errors_formatted)

