"""
Django settings for relational-pulp project.

Generated by 'django-admin startproject' using Django 1.9.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import os
import socket
import sys

import yaml

from pulp.platform import logs

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*u&ouzf)09#*dnm8t9jxahz-y=uwe0g&yn9ir-(lj@l*$cc%qo'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

MEDIA_ROOT = '/var/lib/pulp/content/'
DEFAULT_FILE_STORAGE = 'pulp.platform.models.storage.FileSystem'

# Application definition

INSTALLED_APPS = [
    # django stuff
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third-party
    'rest_framework',
    'django_extensions',
    # pulp - loads as 'pulp_platform' app label
    'pulp.platform.apps.PulpPlatformConfig',
]

# This list would normally come in via entry points, but for this
# demo project it's sufficient just to show adding plugins conditionally
# to Django's installed apps when settings is imported.
# XXX Disabled until we figure out plugin loading in platform
# PULP_PLUGINS = ['pulp_rpm.apps.PulpRpmConfig']
PULP_PLUGINS = []
for plugin in PULP_PLUGINS:
    # since the actual list of plugins would come from entry points, we
    # don't really need to do much validation here, just add the
    # discovered plugins to INSTALLED_APPS. We may want similar hooks in
    # urls.py and for API resources to make sure all content types are
    # exposed via views, or potentially do that dynamically by adding
    # behavior to the content unit master class. For now...we'll just
    # add it to INSTALLED_APPS. :)
    INSTALLED_APPS.append(plugin)

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pulp.platform.urls'

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

WSGI_APPLICATION = 'wsgi.application'

REST_FRAMEWORK = {
    'URL_FIELD_NAME': '_href',
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

# A set of default settings to use if the configuration file in
# /etc/pulp/ is missing or if it does not have values for every setting
_DEFAULT_PULP_SETTINGS = {
    'allowed_hosts': [socket.getfqdn()],
    # https://docs.djangoproject.com/en/1.8/ref/settings/#databases
    'databases': {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'pulp',
            'USER': 'pulp',
            'CONN_MAX_AGE': 0,
        },
    },
    # https://docs.djangoproject.com/en/1.8/ref/settings/#logging and
    # https://docs.python.org/3/library/logging.config.html
    'logging': {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {'format': 'pulp: %(name)s:%(levelname)s: %(message)s'},
        },
        'handlers': {
            'syslog': {
                'address': '/dev/log',
                'facility': logs.CompliantSysLogHandler.LOG_DAEMON,
                'class': 'pulp.platform.logs.CompliantSysLogHandler',
                'formatter': 'simple',
            },
        },
        'loggers': {
            'pulp.platform': {
                'handlers': ['syslog'],
                'level': 'INFO',
            },
            'django': {
                'handlers': ['syslog'],
                'level': 'INFO',
            },
        }
    },
}


def merge_settings(default, override):
    """
    Merge override settings into a set of default settings.

    If both default and override have a key that has a dictionary value, these
    dictionaries are merged recursively. If either of the values are _not_ a
    dictionary, the override key's value is used.
    """
    if not override:
        return default
    merged = default.copy()

    for key in override:
        if key in merged:
            if isinstance(default[key], dict) and isinstance(override[key], dict):
                merged[key] = merge_settings(default[key], override[key])
            else:
                merged[key] = override[key]
        else:
            merged[key] = override[key]

    return merged


def load_settings(paths=()):
    """
    Load one or more configuration files, merge them with the defaults, and apply them
    to this module as module attributes.

    Be aware that the order the paths are provided in matters. Settings are repeatedly
    overridden so settings in the last file in the list win.

    :param paths: One or more absolute paths to configuration files in YAML format.
    :type  paths: str or list of str

    :return: The dictionary of merged settings. This is helpful to see what settings
             Pulp is contributing, but is not the full set of settings Django uses,
             as there are a set of Django-provided defaults as well.
    :rtype:  dict
    """
    if not isinstance(paths, (list, tuple)):
        paths = [paths]

    settings = _DEFAULT_PULP_SETTINGS
    for path in paths:
        try:
            with open(path) as config_file:
                config = config_file.read()
                override_settings = yaml.load(config)
                settings = merge_settings(settings, override_settings)
        except (OSError, IOError):
            # Consider adding logging of some kind, potentially to /var/log/pulp
            pass

    for setting_name, setting_value in settings.items():
        setattr(sys.modules[__name__], setting_name.upper(), setting_value)

    return settings


load_settings('/etc/pulp/server.yaml')
