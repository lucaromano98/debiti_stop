# debiti_stop/settings.py

from pathlib import Path
import os
import dj_database_url

# Se usi PyMySQL (consigliato per evitare build native)
try:
    import pymysql  # type: ignore
    pymysql.install_as_MySQLdb()
except Exception:
    pass

# ===========
# BASE
# ===========
BASE_DIR = Path(__file__).resolve().parent.parent

# In produzione, passa la chiave nello .env (DJANGO_SECRET_KEY)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-not-secure")

# In produzione deve essere False
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# Host e CSRF (lista separata da virgole nello .env)
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS", "db-backoffice.it,www.db-backoffice.it"
).split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://db-backoffice.it,https://www.db-backoffice.it"
).split(",")

# ===========
# APP
# ===========
INSTALLED_APPS = [
    # Admin theme (tenere PRIMA di 'django.contrib.admin')
    "jazzmin",

    # Core Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terze parti
    "rest_framework",
    "corsheaders",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tables2",
    "django_filters",
    "storages",  # per Wasabi/S3

    # Le tue app
    "crm",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # CORS deve stare in alto dopo SessionMiddleware
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "debiti_stop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "crm.context_processors.notifiche_sidebar",
            ],
        },
    },
]

WSGI_APPLICATION = "debiti_stop.wsgi.application"

# ===========
# DATABASE
# ===========
# Devi passare DATABASE_URL nello .env (MySQL DO con ssl-mode=REQUIRED)
if "DATABASE_URL" not in os.environ:
    raise RuntimeError("Manca DATABASE_URL nelle variabili d'ambiente (.env.production)")

DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=600)
}
DATABASES["default"]["ENGINE"] = "django.db.backends.mysql"

# ===========
# AUTH / PASSWORD
# ===========
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ===========
# LINGUA / FUSO
# ===========
LANGUAGE_CODE = "it-it"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True

# ===========
# STATICI & MEDIA (upload su Wasabi)
# ===========
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # serve per collectstatic

# I file caricati vanno su Wasabi via django-storages (S3 compatibile)
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "eu-central-1")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL")  # es: https://s3.eu-central-1.wasabisys.com
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

# ===========
# LOGIN / REDIRECT
# ===========
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

# ===========
# CORS (stringhe separate da virgola nello .env; default: i tuoi domini)
# ===========
# Esempio .env: CORS_ALLOWED_ORIGINS=https://db-backoffice.it,https://www.db-backoffice.it
_cors = os.getenv(
    "CORS_ALLOWED_ORIGINS", "https://db-backoffice.it,https://www.db-backoffice.it"
)
CORS_ALLOWED_ORIGINS = [o for o in _cors.split(",") if o]
CORS_ALLOW_CREDENTIALS = True

# ===========
# REST FRAMEWORK / JWT
# ===========
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    )
}

# ===========
# EMAIL (per ora console; metti un backend SMTP via .env quando servirà)
# ===========
EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

# ===========
# SECURE HEADERS (buon senso per HTTPS dietro Nginx)
# ===========
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True") == "True"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True") == "True"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
