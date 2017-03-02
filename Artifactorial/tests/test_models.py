# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2017 Rémi Duraffort
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

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from Artifactorial.models import Artifact, Directory, AuthToken, Share

import pytest


@pytest.fixture
def users(db):
    group1 = Group.objects.create(name="grp1")
    group2 = Group.objects.create(name="grp2")
    user1 = User.objects.create_user("user1", "user1@example.com", "123456")
    user2 = User.objects.create_user("user2", "user2@example.com", "123456")
    user3 = User.objects.create_user("user3", "user3@example.com", "123456")

    return {"u": [user1, user2, user3],
            "g": [group1, group2]}


class TestAuthToken(object):
    def test_str(self, users):
        token = AuthToken.objects.create(user=users["u"][0])
        assert token.description == ""
        assert len(token.secret) == 32
    
        assert str(token) == "%s ()" % users["u"][0].get_full_name()


class TestDirectory(object):
    def test_str(self, users):
        directory = Directory.objects.create(path="/home/user1", user=users["u"][0])
        assert str(directory) == "/home/user1 (user: %s)" % users["u"][0]

        directory = Directory.objects.create(path="/home/user2", user=users["u"][0])
        assert str(directory) == "/home/user2 (user: %s)" % users["u"][0]

        directory = Directory.objects.create(path="/home/groups/1", group=users["g"][0])
        assert str(directory) == "/home/groups/1 (group: %s)" % users["g"][0]

        directory = Directory.objects.create(path="/pub", is_public=True)
        assert str(directory) == "/pub (anonymous)"

        directory = Directory.objects.create(path="/pub/private")
        assert str(directory) == "/pub/private (anonymous)"

    def test_path_uniqueness(self, users):
        directory = Directory.objects.create(path="/home/user1", user=users["u"][0])
        with pytest.raises(IntegrityError):
            directory = Directory.objects.create(path="/home/user1", user=users["u"][0])

    def test_clean(self, users):
        # group or user but not both
        directory = Directory.objects.create(path="/pub", user=users["u"][0], group=users["g"][0])
        with pytest.raises(ValidationError):
            directory.clean()

        # Path should be absolute
        directory = Directory.objects.create(path="users/1", group=users["g"][0])
        with pytest.raises(ValidationError):
            directory.clean()

        # Path should be normalized
        directory = Directory.objects.create(path="/pub/bla/../blo", user=users["u"][0])
        with pytest.raises(ValidationError):
            directory.clean()
        directory = Directory.objects.create(path="/private/", user=users["u"][0])
        with pytest.raises(ValidationError):
            directory.clean()

        # A valid directory
        directory = Directory.objects.create(path="/private", user=users["u"][0])
        directory.clean()

    def test_absolute_url(self, users):
        directory = Directory.objects.create(path="/home/user1", user=users["u"][0])
        assert directory.get_absolute_url() == "/artifacts/home/user1/"
        directory = Directory.objects.create(path="/pub/bla/bla/bla", is_public=True)
        assert directory.get_absolute_url() == "/artifacts/pub/bla/bla/bla/"
