# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2014-2017 Rémi Duraffort
# Copyright 2017-present Linaro Limited
#
# Author: Rémi Duraffort <remi.duraffort@linaro.org>
#
# SPDX-License-Identifier: MIT

from django.conf import settings
from django.core.management.base import BaseCommand
from Artifactorial.models import Directory

import errno
import os


class Command(BaseCommand):
    args = None
    help = "Clean old files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--purge",
            dest="purge",
            action="store_true",
            default=False,
            help="Also remove permanent artifacts",
        )
        parser.add_argument("--ttl", default=None, help="Override directory TTL")

    def handle(self, *args, **kwargs):
        self.stdout.write("Removing old files in:\n")
        for directory in Directory.objects.all():
            self.stdout.write("* %s\n" % directory.path)
            directory.clean_old_files(kwargs["purge"], kwargs["ttl"])

        self.stdout.write("Removing empty directories:\n")
        for root, _, _ in os.walk(settings.MEDIA_ROOT, topdown=False):
            try:
                os.rmdir(root)
            except OSError as exc:
                if exc.errno != errno.ENOTEMPTY:  # pragma: no cover
                    self.stderr.write("Unable to remove %s: %s\n" % (root, exc))
            else:
                self.stdout.write("* %s\n" % root)
