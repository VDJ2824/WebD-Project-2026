import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'z45(m5+f@q32e)cm!%9x8v*bro0#d0aa07)ewq58+dc3*$x_i#'

DEBUG = False

ALLOWED_HOSTS = ['*']

LOGIN_URL = 'login'

# ✅ FIXED APPS
INSTALLED_APPS = [
    'django.contrib.admin',        # optional but good
    'django.contrib.auth',         # ✅ REQUIRED
    'django.contrib.contenttypes', # ✅ REQUIRED
    'django.contrib.sessions',     # ✅ REQUIRED
    'django.contrib.messages',     # optional
    'django.contrib.staticfiles',

    'app',
]

# ✅ FIXED MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',  # ✅ REQUIRED

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',  # ✅ REQUIRED
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR.parent / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',  # ✅ REQUIRED
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}
]

# ✅ REQUIRED FOR SESSIONS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR.parent / 'static']