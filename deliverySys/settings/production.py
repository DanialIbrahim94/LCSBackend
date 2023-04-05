from .base import *
from decouple import config, Csv


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default=[])


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


# Coupons
MINIMUM_COUPONS_AMOUNT = 40


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT')
    }
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


CORS_ORIGIN_WHITELIST = ['https://www.getcustomerdata.com']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Email configuration

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_PORT = config('EMAIL_PORT')
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer'
    ]
}