# Pinned by digest so Dependabot opens a PR (and CI rebuilds) whenever Debian
# republishes trixie-slim, e.g. with security fixes.
FROM debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

LABEL maintainer="Daniel Wagner <wagi@monom.org>"

ENV DEBIAN_FRONTEND=noninteractive

# Install Python, then the pinned dependencies from requirements.txt into a
# venv (keeps pip from fighting Debian's own python3-* packages)
RUN apt-get update -q && \
    apt-get install --no-install-recommends --yes python3 python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

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
