# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2014-2017 Rémi Duraffort
# Copyright 2017-present Linaro Limited
#
# Author: Rémi Duraffort <remi.duraffort@linaro.org>
#
# SPDX-License-Identifier: MIT

from django.contrib import admin
from django.template.defaultfilters import filesizeformat

from Artifactorial.models import AuthToken, Artifact, Directory, Share

import datetime


class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "description")


class ArtifactAdmin(admin.ModelAdmin):
    def ttl(self, obj):
        return obj.created_at + datetime.timedelta(days=obj.directory.ttl)

    def size(self, obj):
        return filesizeformat(obj.path.size)

    def full_path(self, obj):
        return "/" + obj.path.name

    list_display = (
        "full_path",
        "size",
        "directory",
        "is_permanent",
        "created_at",
        "ttl",
    )
    list_filter = ("directory",)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ("directory",)
        return ()


class DirectoryAdmin(admin.ModelAdmin):
    def current_size(self, obj):
        return "%s / %s" % (filesizeformat(obj.size()), filesizeformat(obj.quota))

    list_display = ("path", "user", "group", "is_public", "ttl", "current_size")


class ShareAdmin(admin.ModelAdmin):
    def artifact_name(self, obj):
        return "/" + obj.artifact.path.name

    list_display = ("artifact_name", "token")
    ordering = ("artifact__path", "token")


admin.site.register(AuthToken, AuthTokenAdmin)
admin.site.register(Artifact, ArtifactAdmin)
admin.site.register(Directory, DirectoryAdmin)
admin.site.register(Share, ShareAdmin)
