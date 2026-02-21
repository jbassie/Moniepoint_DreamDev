"""
Django settings for moniepoint project.

This module contains all Django configuration settings for the Analytics API.
It loads database credentials from environment variables and configures
the application for production use.
"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR: Path = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY: str = os.getenv(
    'SECRET_KEY',
    'django-insecure-l43=20y6&=yly!brdzhs8(ls5xw=xbz*(vgz4k!=4t31-rb4d!'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG: bool = os.getenv('DEBUG', 'True').lower() == 'true'


# Database configuration from environment variables
# Supports both API_database_* and LOCAL_DATABASE_* variable names
# Defaults provided for local development
API_database_name: str = os.getenv("LOCAL_DATABASE_NAME", "moniepoint")
API_database_password: str = os.getenv("LOCAL_DATABASE_PASSWORD", "")
API_database_host: str =os.getenv("API_database_host") or os.getenv("LOCAL_DATABASE_HOST", "localhost")
API_database_username: str = os.getenv("LOCAL_DATABASE_USERNAME", "postgres")
API_database_port: str =  os.getenv("LOCAL_DATABASE_PORT", "5432")

ALLOWED_HOSTS: list[str] = ['*']  # Allow all hosts for hackathon submission


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    #External Apps
    "rest_framework",

    #Project Apps
    "analytics"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'moniepoint.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'moniepoint.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES: Dict[str, Dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": API_database_name,
        "USER": API_database_username,
        "PASSWORD": API_database_password,
        "HOST": API_database_host,
        "PORT": API_database_port,
        # Optimize for 2GB RAM server
        "CONN_MAX_AGE": 300,  # Reuse connections for 5 minutes
        "CONN_HEALTH_CHECKS": True,  # Verify connections before use
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",  # 30 second query timeout
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL: str = 'static/'

# REST Framework configuration
REST_FRAMEWORK: Dict[str, Any] = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}
