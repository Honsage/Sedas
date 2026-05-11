from decouple import config

from .base import *

DEBUG = False

SECRET_KEY = config("SECRET_KEY")

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="sedas"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# CSRF
CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1"
]

if ALLOWED_HOSTS:
    for host in ALLOWED_HOSTS:
        if isinstance(host, str) and not host.startswith("http"):
            CSRF_TRUSTED_ORIGINS.append(f"http://{host}")
            CSRF_TRUSTED_ORIGINS.append(f"https://{host}")
