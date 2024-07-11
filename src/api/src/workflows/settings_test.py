import os

from pathlib import Path

# List of all acceptable ENV values
ENVS = ["LOCAL", "DEV", "STAGE", "PROD"]

# The environment in which the application is currently deployed
ENV = os.environ.get("ENV")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "abcdefg"

# SECURITY WARNING: don't run with debug turned on in production!
LOG_LEVEL = os.environ.get("LOG_LEVEL")
DEBUG = True if ENV != "PROD" else False

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': True,
#     'handlers': {
#         'file': {
#             'level': LOG_LEVEL,
#             'class': 'logging.FileHandler',
#             'filename': f'./logs/{LOG_LEVEL}.logs',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file'],
#             'level': LOG_LEVEL,
#             'propagate': True,
#         },
#     },
# }

# Set allowed hosts by env
ALLOWED_HOSTS = ['*']


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'rest_framework',
    # 'corsheaders',
    'backend',
]

MIDDLEWARE = [
    # 'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# TODO make more restrictive by implementing the CORS_ORIGIN_WHITELIST
# CORS_ALLOW_ALL_ORIGINS = True

CORS_ORIGIN_WHITELIST = ()
# that are not located at .tapis.io to run this api
if ENV == "LOCAL":
    CORS_ORIGIN_WHITELIST = ("localhost", "127.0.0.1")
elif ENV == "DEV":
    CORS_ORIGIN_WHITELIST = ("localhost", "127.0.0.1")
elif ENV == "STAGE":
    CORS_ORIGIN_WHITELIST  = ("localhost", "127.0.0.1")
elif ENV == "PROD":
    CORS_ORIGIN_WHITELIST = ("localhost", "127.0.0.1")
else:
    raise Exception(f"Invalid ENV set. Recieved '{ENV}' Expected oneOf: {ENVS}")

ROOT_URLCONF = 'workflows.urls'

# Set url prefix based on env
URL_PREFIX = "" if ENV == "LOCAL" else "v3/workflows/"

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

WSGI_APPLICATION = 'workflows.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'