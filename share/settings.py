import contextlib
import os
import pathlib

import yaml

DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = ["*"]
STATIC_ROOT = "/app/static"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "artifactorial"),
        "USER": os.environ.get("POSTGRES_USER", "artifactorial"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

WHITENOISE_KEEP_ONLY_HASHED_FILES = True
# STORAGES (Django 4.2+), not the deprecated STATICFILES_STORAGE --
# still works today but STORAGES is the current, non-legacy setting.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Load settings from the configuration file
with contextlib.suppress(FileNotFoundError):
    data = pathlib.Path("/etc/artifactorial.yaml").read_text(encoding="utf-8")
    for k, v in yaml.safe_load(data).items():
        globals()[k] = v

# Add sentry if SENTRY_DSN is defined
if "SENTRY_DSN" in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], integrations=[DjangoIntegration()])
