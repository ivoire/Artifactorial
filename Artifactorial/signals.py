# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2014-2017 Rémi Duraffort
# Copyright 2017-present Linaro Limited
#
# Author: Rémi Duraffort <remi.duraffort@linaro.org>
#
# SPDX-License-Identifier: MIT

from django.db.models.signals import post_delete
from django.dispatch import receiver
from Artifactorial.models import Artifact


@receiver(post_delete, sender=Artifact)
def artifact_post_delete(sender, **kwargs):
    artifact = kwargs["instance"]
    artifact.path.storage.delete(artifact.path.path)
