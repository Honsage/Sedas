from decouple import config

from .base import *

DEBUG = False

SECRET_KEY = config("SECRET_KEY")

ALLOWED_HOSTS = config("ALLOWED_HOSTS").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

if ALLOWED_HOSTS:
    for host in ALLOWED_HOSTS:
        if isinstance(host, str) and not host.startswith("http"):
            CSRF_TRUSTED_ORIGINS.append(f"http://{host}")
            CSRF_TRUSTED_ORIGINS.append(f"https://{host}")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
