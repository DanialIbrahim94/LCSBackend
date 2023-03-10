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


# Coupons
MINIMUM_COUPONS_AMOUNT = 40
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
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'webd25479@gmail.com'
EMAIL_HOST_PASSWORD = 'xfzhpownsjzjxhhr'
