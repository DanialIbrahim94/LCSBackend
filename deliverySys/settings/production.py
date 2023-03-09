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
