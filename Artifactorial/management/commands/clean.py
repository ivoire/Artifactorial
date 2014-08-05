from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from Artifactorial.models import Directory

from optparse import make_option


class Command(BaseCommand):
    args = None
    help = 'Clean old files'

    def handle(self, *args, **kwargs):
        for directory in Directory.objects.all():
            directory.clean_old_files()
