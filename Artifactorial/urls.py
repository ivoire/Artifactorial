# -*- coding: utf-8 -*-
# vim: set ts=4
from __future__ import unicode_literals

from django.conf.urls import patterns, url


urlpatterns = patterns('Artifactorial.views',
                       url(r'^(?P<filename>.*)$', 'root', name='root'))
