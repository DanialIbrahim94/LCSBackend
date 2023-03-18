import os
from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG').upper() == 'TRUE'

ALLOWED_HOSTS = []


# WooCommerce
WOOCOMMERCE_URL = os.environ.get('WOOCOMMERCE_URL')
WOOCOMMERCE_CONSUMER_KEY = os.environ.get('WOOCOMMERCE_CONSUMER_KEY')
WOOCOMMERCE_CONSUMER_SECRET = os.environ.get('WOOCOMMERCE_CONSUMER_SECRET')
WOOCOMMERCE_VERSION = os.environ.get('WOOCOMMERCE_VERSION')
WOOCOMMERCE_PRODUCT_ID = os.environ.get('WOOCOMMERCE_PRODUCT_ID')
WOOCOMMERCE_PAYMENT_METHOD = os.environ.get('WOOCOMMERCE_PAYMENT_METHOD')
WOOCOMMERCE_PAYMENT_METHOD_TITLE = os.environ.get('WOOCOMMERCE_PAYMENT_METHOD_TITLE')
WOOCOMMERCE_PRODUCT_VARIATIONS = {
    100: os.environ('WOOCOMMERCE_PRODUCT_VARIATIONS_100'),
    250: os.environ('WOOCOMMERCE_PRODUCT_VARIATIONS_250'),
    500: os.environ('WOOCOMMERCE_PRODUCT_VARIATIONS_500'),
    1000: os.environ('WOOCOMMERCE_PRODUCT_VARIATIONS_1000'),
    2500: os.environ('WOOCOMMERCE_PRODUCT_VARIATIONS_2500')
}


# Coupons
MINIMUM_COUPONS_AMOUNT = 40

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {

}


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')


CORS_ORIGIN_WHITELIST = []


# Email configuration

EMAIL_BACKEND = ''
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 0
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = ''
RECIPIENT_ADDRESS = ''
