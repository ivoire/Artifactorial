FROM debian:buster-slim

LABEL maintainer="Rémi Duraffort <remi.duraffort@linaro.org>"

ENV DEBIAN_FRONTEND noninteractive

# Install dependencies
RUN apt-get update -q && \
    apt-get install --no-install-recommends --yes gunicorn3 python3 python3-pip python3-yaml && \
    python3 -m pip install --upgrade "django>=2.2,<=2.3" whitenoise && \
    # Cleanup
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create the django project
WORKDIR /app/
RUN chmod 775 /app ;\
    django-admin startproject website /app

# Add entrypoint
COPY share/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Add sources
COPY Artifactorial/ /app/Artifactorial/
COPY share/settings.py /app/website/custom_settings.py
COPY share/urls.py /app/website/urls.py

# Setup application
RUN echo "INSTALLED_APPS.append(\"Artifactorial\")" >> /app/website/settings.py && \
    echo "from Artifactorial.settings import *" >> /app/website/settings.py && \
    echo "from website.custom_settings import *" >> /app/website/settings.py && \
    # Migrate and collect static files
    python3 manage.py collectstatic --noinput
