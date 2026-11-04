"""Configuración de pruebas: reemplaza DATABASES antes de inicializar Django."""
from config.settings import *  # noqa: F403

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:',
    'TEST': {'NAME': ':memory:'},
}}
SECRET_KEY = 'clave-exclusiva-de-pruebas-aisladas-con-longitud-suficiente'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': SECRET_KEY}
DEBUG = False
ALLOWED_HOSTS = ['testserver', 'localhost']
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
LOGGING = {}
