from .base import *

DEBUG = False

ADMINS = (
    ('RunHuaOil', 'crh799250413@gmail.com'),
)

ALLOWED_HOSTS = ['www.educa.com', '.educa.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'educa',
        'USER': 'educa',
        'PASSWORD': 'aa123456',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True

DEFAULT_FROM_EMAIL = ''
EMAIL_HOST = 'smtp.qq.com'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587
EMAIL_USE_TLS = True