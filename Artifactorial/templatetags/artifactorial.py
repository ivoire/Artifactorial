# vim: set ts=4
#
# Copyright 2026 Daniel Wagner
#
# SPDX-License-Identifier: MIT

from django import template

from Artifactorial import __version__

register = template.Library()

RELEASES_URL = "https://github.com/igaw/Artifactorial/releases/tag/v"


@register.simple_tag
def artifactorial_version():
    return __version__


@register.simple_tag
def artifactorial_release_url():
    return RELEASES_URL + __version__
