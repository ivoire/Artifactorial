# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2014-2017 Rémi Duraffort
# Copyright 2017-present Linaro Limited
#
# Author: Rémi Duraffort <remi.duraffort@linaro.org>
#
# SPDX-License-Identifier: MIT

from django.contrib.auth import views as v_auth
from django.conf.urls import url
from django.urls import reverse_lazy

import Artifactorial.views as a_views


urlpatterns = [
    url(r"^$", a_views.home, name="home"),
    # Authentication
    url(
        r"^accounts/login/$",
        v_auth.LoginView.as_view(template_name="Artifactorial/accounts/login.html"),
        name="accounts.login",
    ),
    url(
        r"^accounts/logout/$",
        v_auth.LogoutView.as_view(
            template_name="Artifactorial/accounts/logged_out.html"
        ),
        name="accounts.logout",
    ),
    url(
        r"^accounts/password/change/$",
        v_auth.PasswordChangeView.as_view(success_url=reverse_lazy("accounts.profile")),
        name="accounts.password_change",
    ),
    url(r"^accounts/profile/$", a_views.profile, name="accounts.profile"),
    # Artifacts interactions
    url(r"^artifacts/$", a_views.artifacts, name="artifacts.root"),
    url(r"^artifacts/(?P<filename>.*)$", a_views.artifacts, name="artifacts"),
    # Directories
    url(r"^directories/$", a_views.directories, name="directories.index"),
    # Shares
    url(r"^shares/$", a_views.shares_root, name="shares.root"),
    url(r"^shares/(?P<token>.*)$", a_views.shares, name="shares"),
    # Tokens
    url(r"^tokens/$", a_views.tokens, name="tokens.index"),
    url(r"^tokens/(?P<id>\d+)/delete/$", a_views.tokens_delete, name="tokens.delete"),
]
