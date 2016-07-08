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

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import datetime, utc

import binascii
from datetime import timedelta
import os


def random_hash():
    """ Create a random string of size 32 """
    return binascii.b2a_hex(os.urandom(16))


@python_2_unicode_compatible
class AuthToken(models.Model):
    user = models.ForeignKey(User, blank=False)
    secret = models.TextField(max_length=32, unique=True, default=random_hash)
    description = models.TextField(null=False, blank=True)

    def __str__(self):
        return "%s (%s)" % (self.user.get_full_name(), self.description)


@python_2_unicode_compatible
class Directory(models.Model):
    path = models.CharField(max_length=300, null=False, blank=False)
    user = models.ForeignKey(User, null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    ttl = models.IntegerField(blank=False, default=90,
                              help_text="Files TTL in days")
    quota = models.IntegerField(blank=False, default=1024*1024*1024,
                                help_text='Size limit in Bytes')

    class Meta:
        verbose_name_plural = 'Directories'

    def clean(self):
        """
        Artifacts should be owned by one group or one user, not both.
        """
        if self.user is not None and self.group is not None:
            raise ValidationError("Cannot be owned by user and group")
        if not os.path.normpath(self.path) == self.path:
            raise ValidationError({'path': ['Expecting a normalized path and '
                                            'no trailing slashes']})
        if not os.path.isabs(self.path):
            raise ValidationError({'path': ['Expecting an absolute path']})

    def __str__(self):
        if self.user is not None:
            return "%s (%s)" % (self.path, self.user.get_full_name())
        elif self.group is not None:
            return "%s (%s)" % (self.path, self.group)
        else:
            return "%s (anonymous)" % (self.path)

    @models.permalink
    def get_absolute_url(self):
        return ("artifacts", [self.path[1:] + '/'])

    def is_visible_to(self, user):
        """
        Check that the current directory is visible to the current user
        A public directory is visible to all.
        An anonymous directory is visible to all active users.

        :param user: the user to check
        :return: True if the directory is visible to the user, False otherwise.
        """
        if self.is_public:
            return True
        if self.user is not None:
            return self.user == user
        elif self.group is not None:
            return self.group in user.groups.all()
        else:
            return user.is_active

    def is_writable_to(self, user):
        """
        Check that the user can write to the current directory
        An anonymous directory is writable to all.

        :param user: the user to check
        :return: True if the user can write to this directory, False otherwise.
        """
        if self.user is not None:
            return self.user == user
        elif self.group is not None:
            return self.group in user.groups.all()
        else:
            return True

    def size(self):
        size = 0
        for artifact in self.artifact_set.all():
            size += artifact.path.size
        return size

    def clean_old_files(self):
        # A negative TTL mean that we should not remove old files
        if self.ttl < 0:
            return
        now = datetime.utcnow().replace(tzinfo=utc)
        older_than = now - timedelta(days=self.ttl)
        self.artifact_set.filter(created_at__lt=older_than)\
                         .exclude(is_permanent=True)\
                         .delete()

    def purge_old_files(self, ttl, permanent):
        now = datetime.utcnow().replace(tzinfo=utc)
        older_than = now - timedelta(days=ttl)
        query = self.artifact_set.filter(created_at__lt=older_than)
        # Don't remove permanent files by default
        if not permanent:
            query = query.exclude(is_permanent=True)
        query.delete()


def get_path_name(instance, filename):
    base_path = ''
    if not instance.is_permanent:
        now = datetime.now()
        base_path = now.strftime('%Y/%m/%d/%H/%M')
    return os.path.normpath('/'.join([instance.directory.path,
                                      base_path, filename])).strip('/')


@python_2_unicode_compatible
class Artifact(models.Model):
    path = models.FileField(upload_to=get_path_name)
    directory = models.ForeignKey(Directory, blank=False)
    is_permanent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.path.name

    @models.permalink
    def get_absolute_url(self):
        return ("artifacts", [self.path.name])

    def is_visible_to(self, user):
        return self.directory.is_visible_to(user)


@python_2_unicode_compatible
class Share(models.Model):
    token = models.TextField(max_length=32, unique=True, default=random_hash)
    artifact = models.ForeignKey(Artifact, blank=False)

    def __str__(self):
        return "%s -> %s" % (self.token, self.artifact)

    @models.permalink
    def get_absolute_url(self):
        return ("shared", [self.token])
