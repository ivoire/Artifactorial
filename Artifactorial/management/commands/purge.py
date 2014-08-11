# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2014 Rémi Duraffort
# This file is part of Artifactorial.
#
# Artifactorial is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Artifactorial is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Artifactorial.  If not, see <http://www.gnu.org/licenses/>

from __future__ import unicode_literals

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
