from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv
from corsheaders.defaults import default_headers, default_methods

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

# --- Apps ---
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceiros
    "corsheaders",
    "rest_framework",

    # App
    "todos",
]


MIDDLEWARE = [
  "corsheaders.middleware.CorsMiddleware",
  "django.middleware.security.SecurityMiddleware",
  "django.contrib.sessions.middleware.SessionMiddleware",
  "django.middleware.common.CommonMiddleware",
  "django.middleware.csrf.CsrfViewMiddleware",
  "django.contrib.auth.middleware.AuthenticationMiddleware",
  "django.contrib.messages.middleware.MessageMiddleware",
  "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- CORS / CSRF ---
# Read from env (comma-separated) or fall back to sane defaults
_default_cors_origins = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:19006",
    "http://localhost:19006",
    "http://127.0.0.1:8081",
    "http://localhost:8081",
    "http://localhost:8082",
]
_cors_env = os.getenv("CORS_ALLOWED_ORIGINS")
if _cors_env:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    CORS_ALLOWED_ORIGINS = _default_cors_origins

# Quando estiver em modo de desenvolvimento, garanta que as origens locais
# comumente usadas pelo frontend (Expo/React Native web) permaneçam liberadas.
if DEBUG:
    _dev_extra_origins = {
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8081",
        "http://localhost:8081",
        "http://127.0.0.1:8082",
        "http://localhost:8082",
        "http://127.0.0.1:19006",
        "http://localhost:19006",
    }
    CORS_ALLOWED_ORIGINS = sorted(set(CORS_ALLOWED_ORIGINS) | _dev_extra_origins)

# Only apply CORS headers to API URLs
CORS_URLS_REGEX = r"^/api/.*$"

# Allow cookies/authorization across origins when needed
CORS_ALLOW_CREDENTIALS = True

# Allow common custom headers used by browsers/frameworks
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-requested-with",
]

# Allow standard HTTP methods
CORS_ALLOW_METHODS = list(default_methods)

CSRF_TRUSTED_ORIGINS = []
for origin in CORS_ALLOWED_ORIGINS:
    if origin.startswith("http://") or origin.startswith("https://"):
        CSRF_TRUSTED_ORIGINS.append(origin)

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

ROOT_URLCONF = "server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "server.wsgi.application"

# --- Banco ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Localização ---
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# --- Static ---
STATIC_URL = "static/"

# --- DRF + JWT ---
ACCESS_MIN = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
REFRESH_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "EXCEPTION_HANDLER": "todos.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=ACCESS_MIN),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=REFRESH_DAYS),
}

# --- E-mail (console por padrão; token sai no terminal) ---
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@datacake.local")


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "[%(asctime)s] [%(levelname)s] %(name)s :: %(message)s "
                "(in %(pathname)s:%(lineno)d)"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {"format": "[%(levelname)s] %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "simple",
        },
    },
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": True},
        "todos": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "": {"handlers": ["console"], "level": "INFO"},
    },
}
