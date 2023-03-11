from django.conf import settings

from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import User, Role, Business, Coupons, CouponHistory, DownHistory


class RoleSerializer(serializers.ModelSerializer):
	class Meta:
		model = Role
		fields = ('id', 'roleType')

class BusinessSerializer(serializers.ModelSerializer):
	class Meta:
		model = Business
		fields = ('id', 'businessType')

class UserSerializer(serializers.ModelSerializer):
    business = BusinessSerializer(required=True)
    role = RoleSerializer(required=True)
    coupons_amount = serializers.SerializerMethodField()
    coupons_minimum_amount = serializers.SerializerMethodField()

    def get_coupons_amount(self, obj):
        return Coupons.objects.filter(user=obj).count()

    def get_coupons_minimum_amount(self, obj):
        return settings.MINIMUM_COUPONS_AMOUNT

    class Meta:
        model = User
        fields = ('id', 'fullName', 'email', 'phone', 'address', 'birthday', 'business', 'role', 'couponCount', 'password', 'coupons_amount', 'coupons_minimum_amount')

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'fullName', 'email', 'phone', 'address', 'birthday', 'business', 'role', 'couponCount', 'password')

class LoginSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    class Meta:
        model = User
        fields = ('token', 'id', 'fullName', 'email', 'phone', 'address', 'birthday', 'businessId', 'couponCount', 'password', 'roleId')
	
class SignUpSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('token', 'email', 'password')

class CouponSerializer(serializers.ModelSerializer):
	class Meta:
		model = Coupons
		fields = ('id', 'code', 'user', 'used')
                
class CouponHistorySerializer(serializers.ModelSerializer):
	class Meta:
		model = CouponHistory
		fields = ('id', 'fullName', 'email', 'couponCount', 'createdAt', 'createdBy')
                
class DownHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DownHistory
        fields = ('id', 'from_user', 'down_user')
