from .base import *
from decouple import config, Csv


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default=[])
CORS_ORIGIN_ALLOW_ALL = True


# WooCommerce
WOOCOMMERCE_URL = config('WOOCOMMERCE_URL')
WOOCOMMERCE_CONSUMER_KEY = config('WOOCOMMERCE_CONSUMER_KEY')
WOOCOMMERCE_CONSUMER_SECRET = config('WOOCOMMERCE_CONSUMER_SECRET')
WOOCOMMERCE_VERSION = config('WOOCOMMERCE_VERSION', 'wc/v3')

WOOCOMMERCE_PRODUCT_ID = config('WOOCOMMERCE_PRODUCT_ID')
WOOCOMMERCE_PAYMENT_METHOD = config('WOOCOMMERCE_PAYMENT_METHOD')
WOOCOMMERCE_PAYMENT_METHOD_TITLE = config('WOOCOMMERCE_PAYMENT_METHOD_TITLE')
WOOCOMMERCE_PRODUCT_VARIATIONS = {
    100: config('WOOCOMMERCE_PRODUCT_VARIATIONS_100', cast=int),
    250: config('WOOCOMMERCE_PRODUCT_VARIATIONS_250', cast=int),
    500: config('WOOCOMMERCE_PRODUCT_VARIATIONS_500', cast=int),
    1000: config('WOOCOMMERCE_PRODUCT_VARIATIONS_1000', cast=int),
    2500: config('WOOCOMMERCE_PRODUCT_VARIATIONS_2500', cast=int)
}


# JOTFORM API
JOTFORM_API_KEY = config('JOTFORM_API_KEY')


# Coupons
MINIMUM_COUPONS_AMOUNT = config('MINIMUM_COUPONS_AMOUNT', cast=int, default=50)
SEND_RECHARGE_REQUEST_COOLDOWN = 15 # in days

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = []


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Email configuration

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
