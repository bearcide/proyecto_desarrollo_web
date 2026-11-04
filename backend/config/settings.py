"""
Configuración Django del backend SaaS B2B (API REST, 100% JSON).

Toda la configuración variable o sensible se lee de variables de entorno
(Azure App Service > Configuration > Application settings). En local se
carga desde un archivo .env (ver .env.example).
"""
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
_env_file = BASE_DIR / '.env'
if _env_file.exists():  # En Azure no existe: las variables vienen del App Service.
    environ.Env.read_env(_env_file)


# ---------------------------------------------------------------------------
# Seguridad y hosts
# ---------------------------------------------------------------------------
SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-clave-para-desarrollo-local-12345')
DEBUG = env.bool('DJANGO_DEBUG', default=True)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])
CSRF_TRUSTED_ORIGINS = env.list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[])

# Azure App Service publica su hostname en WEBSITE_HOSTNAME.
_azure_host = env('WEBSITE_HOSTNAME', default='')
if _azure_host:
    ALLOWED_HOSTS.append(_azure_host)
    CSRF_TRUSTED_ORIGINS.append(f'https://{_azure_host}')

if not DEBUG:
    # Azure termina TLS en el balanceador y reenvía por HTTP interno.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=False)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int('DJANGO_SECURE_HSTS_SECONDS', default=0)
    SECURE_CONTENT_TYPE_NOSNIFF = True


# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',

    # Locales
    'apps.core',  # O la ruta de tus apps locales
]

MIDDLEWARE = [
    'apps.core.api.problems.ApiProblemMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Debe ir antes de CommonMiddleware.
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# ---------------------------------------------------------------------------
# Base de datos: Soporta SQLite local o PostgreSQL mediante DATABASE_URL
# ---------------------------------------------------------------------------
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Django REST Framework: respuestas únicamente JSON
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.api.problems.problem_exception_handler',
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    # Seguro por defecto: todo endpoint exige autenticación salvo que se declare lo contrario.
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    # JWT (SimpleJWT) como mecanismo de autenticación de la API.
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': env.int('API_PAGE_SIZE', default=25),
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'InscripcionMadeEasy API',
    'DESCRIPTION': 'API RESTful multi-tenant para inscripciones escolares',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,  # La schema la exponemos con una ruta explícita (name='schema').
}


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:5173', 'http://127.0.0.1:5173'],
)
CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=True)


# ---------------------------------------------------------------------------
# Contraseñas, i18n y estáticos
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ---------------------------------------------------------------------------
# Logging a stdout (Azure App Service > Log stream)
# ---------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '{asctime} {levelname} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': env('DJANGO_LOG_LEVEL', default='INFO')},
    'loggers': {
        'apps.core.auditoria': {
            'handlers': ['console'], 'level': 'INFO', 'propagate': False,
        },
    },
}

# El selector es contexto solicitado; el servicio verifica la membresía.
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = (*default_headers, 'x-tenant-id')
