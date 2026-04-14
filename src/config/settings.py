"""
Django settings for The Nexus Freelancing Platform.

Production checklist: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
All secrets are loaded from .env via python-decouple.
"""
import os
import logging
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Core ─────────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
DEBUG       = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ── Installed apps ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Project apps
    'Apps.accounts',
    'Apps.contracts',
    'Apps.freelancers',
    'Apps.jobs',
    'Apps.messaging',
    'Apps.proposals',
    'Apps.reviews',
    'Apps.wallet',
    'Apps.api',

    # Third-party
    'import_export',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',   # #16: JWT blacklist on logout
    'corsheaders',                                  # #24: CORS for mobile/API clients
]

# ── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',          # CORS — must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────────────
# Development: SQLite (default)
# Production: set DB_ENGINE=django.db.backends.postgresql in .env
DATABASES = {
    'default': {
        'ENGINE':   config('DB_ENGINE',   default='django.db.backends.sqlite3'),
        'NAME':     config('DB_NAME',     default=str(BASE_DIR / 'db.sqlite3')),
        'USER':     config('DB_USER',     default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST':     config('DB_HOST',     default=''),
        'PORT':     config('DB_PORT',     default=''),
        # PostgreSQL connection pooling (ignored by SQLite)
        'CONN_MAX_AGE': 60,
    }
}

# ── Auth ──────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# #26: Session timeout — 8 hours (was Django default of 2 weeks)
SESSION_COOKIE_AGE     = config('SESSION_COOKIE_AGE', default=28800, cast=int)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ── Django REST Framework ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '300/hour',
    },
    # #18: Pagination — 20 items per page on all list endpoints
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'Apps.api.exceptions.custom_exception_handler',
}

# #16: JWT — blacklist tokens on logout so revoked tokens can't be reused
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=4),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': True,   # ← was False; revoke old refresh tokens
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ── CORS ─────────────────────────────────────────────────────────────────────
# #24: Allow mobile apps / external clients to call /api/ endpoints
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv(),
)
CORS_URLS_REGEX = r'^/api/.*$'   # Only expose CORS on API routes, not HTML views

# ── Email ─────────────────────────────────────────────────────────────────────
# #8: Email notifications
# Dev: console (prints to terminal). Prod: set EMAIL_BACKEND=smtp in .env
EMAIL_BACKEND      = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST         = config('EMAIL_HOST',     default='smtp.gmail.com')
EMAIL_PORT         = config('EMAIL_PORT',     default=587, cast=int)
EMAIL_USE_TLS      = config('EMAIL_USE_TLS',  default=True, cast=bool)
EMAIL_HOST_USER    = config('EMAIL_HOST_USER',    default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='The Nexus <no-reply@nexus.uz>')

# ── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = config('LANGUAGE_CODE', default='en-us')
TIME_ZONE     = config('TIME_ZONE',     default='Asia/Tashkent')
USE_I18N      = True
USE_TZ        = True

# ── Static & Media ────────────────────────────────────────────────────────────
STATIC_URL     = 'static/'
STATIC_ROOT    = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'logo',
]
MEDIA_URL  = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Security (production) ─────────────────────────────────────────────────────
# #23: HTTPS / security headers — these are safe to enable even in dev.
#      They become mandatory in production.
if not DEBUG:
    SECURE_SSL_REDIRECT             = True
    SECURE_HSTS_SECONDS             = 31536000   # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS  = True
    SECURE_HSTS_PRELOAD             = True
    SESSION_COOKIE_SECURE           = True
    CSRF_COOKIE_SECURE              = True

X_FRAME_OPTIONS        = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── CSRF ──────────────────────────────────────────────────────────────────────
CSRF_FAILURE_VIEW = 'Apps.accounts.views.csrf_failure'

# ── Logging ───────────────────────────────────────────────────────────────────
# #25: Structured logging — console + rotating file
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
        },
        'file_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 10 * 1024 * 1024,   # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
        'file_info': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_error'],
            'level': 'WARNING',
            'propagate': False,
        },
        'Apps': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file_error'],
        'level': 'WARNING',
    },
}
