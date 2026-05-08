from .base import *

SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Suppress password hashing to speed up tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
