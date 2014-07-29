# -*- coding: utf-8 -*-
# vim: set ts=4

from django.conf.urls import include, patterns, url
from django.core.urlresolvers import reverse_lazy


urlpatterns = patterns('Artifactorial.views',
                       url(r'^$', 'index', name='index'),
                       url(r'^post', 'post', name='post'))
