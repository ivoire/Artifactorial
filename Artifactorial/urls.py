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

from django.contrib.auth import views as v_auth
from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy

import Artifactorial.views as a_views


urlpatterns = [
    url(r'^$', a_views.home, name='home'),

    # Authentication
    url(r'^accounts/login/$', v_auth.login, {'template_name': 'Artifactorial/accounts/login.html'}, name='accounts.login'),
    url(r'^accounts/logout/$', v_auth.logout, {'template_name': 'Artifactorial/accounts/logged_out.html'}, name='accounts.logout'),
    url(r'^accounts/password/change/$', v_auth.password_change, {'post_change_redirect': reverse_lazy('accounts.profile')}, name='accounts.password_change'),
    url(r'^accounts/profile/$', a_views.profile, name='accounts.profile'),

    # Artifacts interactions
    url(r'^artifacts/$', a_views.artifacts, name='artifacts.root'),
    url(r'^artifacts/(?P<filename>.*)$', a_views.artifacts, name='artifacts'),

    # Directories
    url(r'^directories/$', a_views.directories, name='directories.index'),

    # Shares
    url(r'^shares/$', a_views.shares_root, name='shares.root'),
    url(r'^shares/(?P<token>.*)$', a_views.shares, name='shares'),

    # Tokens
    url(r'^tokens/$', a_views.tokens, name='tokens.index'),
    url(r'^tokens/(?P<id>\d+)/delete/$', a_views.tokens_delete, name='tokens.delete'),
]
