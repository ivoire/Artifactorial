import contextlib
import os
import pathlib
import yaml

DEBUG = os.environ.get("DEBUG", False)
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

WHITENOISE_KEEP_ONLY_HASHED_FILES = True
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Load settings from the configuration file
with contextlib.suppress(FileNotFoundError):
    data = pathlib.Path("/etc/artifactorial.yaml").read_text(encoding="utf-8")
    for (k, v) in yaml.safe_load(data).items():
        globals()[k] = v

# Add sentry if SENTRY_DSN is defined
if "SENTRY_DSN" in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], integrations=[DjangoIntegration()])
