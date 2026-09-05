# vim: set ts=4
#
# Copyright 2016-2017 Rémi Duraffort
# Copyright 2017-present Linaro Limited
# Copyright 2026 Daniel Wagner
#
# Author: Rémi Duraffort <remi.duraffort@linaro.org>
#
# SPDX-License-Identifier: MIT

from django.apps import AppConfig


class ArtifactorialConfig(AppConfig):
    name = "Artifactorial"
    verbose_name = "Artifactorial"

    def ready(self):
        from Artifactorial import signals  # noqa: F401
