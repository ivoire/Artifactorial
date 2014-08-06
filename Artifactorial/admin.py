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

from django.contrib import admin
from django.template.defaultfilters import filesizeformat

from Artifactorial.models import AuthToken, Artifact, Directory


class ArtifactAdmin(admin.ModelAdmin):
    list_display = ('path', 'directory', 'is_permanent', 'created_at')


class DirectoryAdmin(admin.ModelAdmin):
    def current_size(self, obj):
        return "%s / %s" % (filesizeformat(obj.size()),
                            filesizeformat(obj.quota))

    list_display = ('path', 'user', 'group', 'is_public', 'ttl', 'current_size')


admin.site.register(AuthToken)
admin.site.register(Artifact, ArtifactAdmin)
admin.site.register(Directory, DirectoryAdmin)
