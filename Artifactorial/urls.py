# -*- coding: utf-8 -*-
# vim: set ts=4

from django.conf.urls import patterns, url


urlpatterns = patterns('Artifactorial.views',
                       url(r'^post', 'post', name='post'),
                       url(r'^get(?P<filename>/.*)$', 'get', name='get'))
