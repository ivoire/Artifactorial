# vim: set ts=4
#
# Copyright 2014-2017 Rémi Duraffort
# Copyright 2017-present Linaro Limited
# Copyright 2026 Daniel Wagner
#
# Author: Rémi Duraffort <remi.duraffort@linaro.org>
#
# SPDX-License-Identifier: MIT

from django.contrib.auth import views as v_auth
from django.urls import re_path, reverse_lazy

import Artifactorial.views as a_views

urlpatterns = [
    re_path(r"^$", a_views.home, name="home"),
    # Authentication
    re_path(
        r"^accounts/login/$",
        v_auth.LoginView.as_view(template_name="Artifactorial/accounts/login.html"),
        name="accounts.login",
    ),
    re_path(
        r"^accounts/logout/$",
        v_auth.LogoutView.as_view(
            template_name="Artifactorial/accounts/logged_out.html"
        ),
        name="accounts.logout",
    ),
    re_path(
        r"^accounts/password/change/$",
        v_auth.PasswordChangeView.as_view(success_url=reverse_lazy("accounts.profile")),
        name="accounts.password_change",
    ),
    re_path(r"^accounts/profile/$", a_views.profile, name="accounts.profile"),
    # Artifacts interactions
    re_path(r"^artifacts/$", a_views.artifacts, name="artifacts.root"),
    re_path(r"^artifacts/(?P<filename>.*)$", a_views.artifacts, name="artifacts"),
    # Directories
    re_path(r"^directories/$", a_views.directories, name="directories.index"),
    # Shares
    re_path(r"^shares/$", a_views.shares_root, name="shares.root"),
    re_path(r"^shares/(?P<token>.*)$", a_views.shares, name="shares"),
    # Tokens
    re_path(r"^tokens/$", a_views.tokens, name="tokens.index"),
    re_path(
        r"^tokens/(?P<id>\d+)/delete/$", a_views.tokens_delete, name="tokens.delete"
    ),
]
