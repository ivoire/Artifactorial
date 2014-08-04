from django.core.management.base import BaseCommand
from Artifactorial.models import Directory

from optparse import make_option


class Command(BaseCommand):
    args = None
    help = 'Purge old files'
    option_list = BaseCommand.option_list + (
        make_option('--ttl',
                    dest='TTL',
                    default=90,
                    type=int,
                    help='Time To Live in days'),
        make_option('--all',
                    dest='all',
                    default=False,
                    action="store_true",
                    help='Also remove permanent files'))


    def handle(self, *args, **kwargs):
        for directory in Directory.objects.all():
            directory.purge_old_files(kwargs['TTL'], kwargs['all'])
