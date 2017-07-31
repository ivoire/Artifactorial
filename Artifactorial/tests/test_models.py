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

from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from Artifactorial.models import Artifact, Directory, AuthToken, Share

import binascii
from datetime import timedelta
import os
import pytest
import sys


def bytes2unicode(string):
    if sys.version < "3":
        return string
    else:
        return bytes.decode(string, "utf-8")

@pytest.fixture
def users(db):
    group1 = Group.objects.create(name="grp1")
    group2 = Group.objects.create(name="grp2")
    user1 = User.objects.create_user("user1", "user1@example.com", "123456")
    user1.groups.add(group1, group2)
    user2 = User.objects.create_user("user2", "user2@example.com", "123456")
    user2.groups.add(group1)
    user3 = User.objects.create_user("user3", "user3@example.com", "123456")

    return {"u": [user1, user2, user3],
            "g": [group1, group2]}


class TestAuthToken(object):
    def test_str(self, users):
        token = AuthToken.objects.create(user=users["u"][0])
        assert token.description == ""
        assert len(token.secret) == 32
    
        assert str(token) == "%s ()" % users["u"][0].username
        users["u"][0].first_name = "Hello"
        users["u"][0].save()
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

    def test_quota_min_value(self, db):
        directory = Directory.objects.create(path="/pub", is_public=True, quota=0)
        with pytest.raises(ValidationError):
            directory.full_clean()

    def test_quota_max_value(self, db):
        directory = Directory.objects.create(path="/pub", is_public=True, quota=sys.maxsize)
        directory.full_clean()

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

    def test_visible_writable_to(self, users):
        anon = AnonymousUser()
        directory = Directory.objects.create(path="/anonymous", is_public=False)
        assert directory.is_visible_to(anon) == False
        assert directory.is_visible_to(users["u"][0]) == True
        assert directory.is_visible_to(users["u"][1]) == True
        assert directory.is_visible_to(users["u"][2]) == True
        assert directory.is_writable_to(anon) == True
        assert directory.is_writable_to(users["u"][0]) == True
        assert directory.is_writable_to(users["u"][1]) == True
        assert directory.is_writable_to(users["u"][2]) == True

        directory = Directory.objects.create(path="/pub", is_public=True)
        assert directory.is_visible_to(anon) == True
        assert directory.is_visible_to(users["u"][0]) == True
        assert directory.is_visible_to(users["u"][1]) == True
        assert directory.is_visible_to(users["u"][2]) == True
        assert directory.is_writable_to(anon) == True
        assert directory.is_writable_to(users["u"][0]) == True
        assert directory.is_writable_to(users["u"][1]) == True
        assert directory.is_writable_to(users["u"][2]) == True

        directory = Directory.objects.create(path="/home/user1", user=users["u"][0], is_public=False)
        assert directory.is_visible_to(anon) == False
        assert directory.is_visible_to(users["u"][0]) == True
        assert directory.is_visible_to(users["u"][1]) == False
        assert directory.is_visible_to(users["u"][2]) == False
        assert directory.is_writable_to(anon) == False
        assert directory.is_writable_to(users["u"][0]) == True
        assert directory.is_writable_to(users["u"][1]) == False
        assert directory.is_writable_to(users["u"][2]) == False

        directory = Directory.objects.create(path="/home/user2", user=users["u"][1], is_public=False)
        assert directory.is_visible_to(anon) == False
        assert directory.is_visible_to(users["u"][0]) == False
        assert directory.is_visible_to(users["u"][1]) == True
        assert directory.is_visible_to(users["u"][2]) == False
        assert directory.is_writable_to(anon) == False
        assert directory.is_writable_to(users["u"][0]) == False
        assert directory.is_writable_to(users["u"][1]) == True
        assert directory.is_writable_to(users["u"][2]) == False

        directory.is_public = True
        directory.save()
        assert directory.is_visible_to(anon) == True
        assert directory.is_visible_to(users["u"][0]) == True
        assert directory.is_visible_to(users["u"][1]) == True
        assert directory.is_visible_to(users["u"][2]) == True
        assert directory.is_writable_to(anon) == False
        assert directory.is_writable_to(users["u"][0]) == False
        assert directory.is_writable_to(users["u"][1]) == True
        assert directory.is_writable_to(users["u"][2]) == False

        directory = Directory.objects.create(path="/home/grp1", group=users["g"][0], is_public=False)
        assert directory.is_visible_to(anon) == False
        assert directory.is_visible_to(users["u"][0]) == True
        assert directory.is_visible_to(users["u"][1]) == True
        assert directory.is_visible_to(users["u"][2]) == False
        assert directory.is_writable_to(anon) == False
        assert directory.is_writable_to(users["u"][0]) == True
        assert directory.is_writable_to(users["u"][1]) == True
        assert directory.is_writable_to(users["u"][2]) == False

        directory.is_public = True
        directory.save()
        assert directory.is_visible_to(anon) == True
        assert directory.is_visible_to(users["u"][0]) == True
        assert directory.is_visible_to(users["u"][1]) == True
        assert directory.is_visible_to(users["u"][2]) == True
        assert directory.is_writable_to(anon) == False
        assert directory.is_writable_to(users["u"][0]) == True
        assert directory.is_writable_to(users["u"][1]) == True
        assert directory.is_writable_to(users["u"][2]) == False

        directory = Directory.objects.create(path="/home/grp2", group=users["g"][1], is_public=False)
        assert directory.is_visible_to(anon) == False
        assert directory.is_visible_to(users["u"][0]) == True
        assert directory.is_visible_to(users["u"][1]) == False
        assert directory.is_visible_to(users["u"][2]) == False
        assert directory.is_writable_to(anon) == False
        assert directory.is_writable_to(users["u"][0]) == True
        assert directory.is_writable_to(users["u"][1]) == False
        assert directory.is_writable_to(users["u"][2]) == False

        directory.is_public = True
        directory.save()
        assert directory.is_visible_to(anon) == True
        assert directory.is_visible_to(users["u"][0]) == True
        assert directory.is_visible_to(users["u"][1]) == True
        assert directory.is_visible_to(users["u"][2]) == True
        assert directory.is_writable_to(anon) == False
        assert directory.is_writable_to(users["u"][0]) == True
        assert directory.is_writable_to(users["u"][1]) == False
        assert directory.is_writable_to(users["u"][2]) == False

    def test_quota_progress(self, users):
        directory = Directory.objects.create(path="/home/grp2", group=users["g"][1], quota=500)
        assert directory.size() == 0
        assert directory.quota_progress() == 0

        directory.size = lambda : 50
        assert directory.size() == 50
        assert directory.quota_progress() == 10

        directory.size = lambda : 500
        assert directory.size() == 500
        assert directory.quota_progress() == 100

    def test_clean_old_files(self, users, settings, tmpdir):
        media = tmpdir.mkdir("media")
        settings.MEDIA_ROOT = str(media)
        dir1 = Directory.objects.create(path="/home/user1", user=users["u"][0])
        dir2 = Directory.objects.create(path="/home/user2", user=users["u"][1])
        user1_root = media.mkdir("home").mkdir("user1")
        user2_root = media.join("home").mkdir("user2")

        user1_arts = []
        for (index, f_name) in enumerate(["file1.txt", "testing.py", "hello.jpg"]):
            filename = str(user1_root.join(f_name))
            with open(filename, "w") as f_out:
                f_out.write(bytes2unicode(binascii.b2a_hex(os.urandom(16))))
            art = Artifact.objects.create(directory=dir1, path=filename)
            art.created_at -= timedelta(days=index)
            art.save()
            user1_arts.append(art)
        user2_arts = []
        for (index, f_name) in enumerate(["file2.txt", "bla.py", "world.pdf"]):
            filename = str(user2_root.join(f_name))
            with open(filename, "w") as f_out:
                f_out.write(bytes2unicode(binascii.b2a_hex(os.urandom(16))))
            art = Artifact.objects.create(directory=dir2, path=filename)
            art.created_at -= timedelta(days=index)
            art.save()
            user2_arts.append(art)

        # Test the directory quota while we are here
        assert dir1.size() == 3 * 32
        assert dir2.size() == 3 * 32

        assert dir1.artifact_set.count() == 3
        assert dir2.artifact_set.count() == 3

        # Will not remove anything because the ttl is too long
        dir1.clean_old_files(purge=False)
        dir2.clean_old_files(purge=False)
        assert dir1.artifact_set.count() == 3
        assert dir2.artifact_set.count() == 3

        dir1.ttl = 2
        dir1.save()
        dir1.clean_old_files(purge=False)
        assert dir1.artifact_set.count() == 2
        assert os.path.exists(user1_arts[0].path.path) == True
        assert os.path.exists(user1_arts[1].path.path) == True
        assert os.path.exists(user1_arts[2].path.path) == False
        assert dir2.artifact_set.count() == 3
        assert os.path.exists(user2_arts[0].path.path) == True
        assert os.path.exists(user2_arts[1].path.path) == True
        assert os.path.exists(user2_arts[2].path.path) == True
        dir2.clean_old_files(purge=False, override_ttl=2)
        assert dir2.artifact_set.count() == 2
        assert os.path.exists(user2_arts[0].path.path) == True
        assert os.path.exists(user2_arts[1].path.path) == True
        assert os.path.exists(user2_arts[2].path.path) == False

        # Set a 0 TTL => do not remove anything (unless permanent is True)
        dir2.ttl = 0
        dir2.save()
        dir2.clean_old_files(purge=False)
        assert dir2.artifact_set.count() == 2
        assert os.path.exists(user2_arts[0].path.path) == True
        assert os.path.exists(user2_arts[1].path.path) == True
        assert os.path.exists(user2_arts[2].path.path) == False
        dir2.clean_old_files(purge=True)
        assert dir2.artifact_set.count() == 0
        assert os.path.exists(user2_arts[0].path.path) == False
        assert os.path.exists(user2_arts[1].path.path) == False
        assert os.path.exists(user2_arts[2].path.path) == False

        dir1.clean_old_files(purge=True, override_ttl=1)
        assert dir1.artifact_set.count() == 1
        assert os.path.exists(user1_arts[0].path.path) == True
        assert os.path.exists(user1_arts[1].path.path) == False
        assert os.path.exists(user1_arts[2].path.path) == False
        dir1.clean_old_files(purge=True, override_ttl=0)
        assert dir1.artifact_set.count() == 0
        assert os.path.exists(user1_arts[0].path.path) == False
        assert os.path.exists(user1_arts[1].path.path) == False
        assert os.path.exists(user1_arts[2].path.path) == False


class TestArtifact(object):
    def test_methods(self, users, settings, tmpdir):
        media = tmpdir.mkdir("media")
        settings.MEDIA_ROOT = str(media)
        directory = Directory.objects.create(path="/home/user1", user=users["u"][0])
        user_root = media.mkdir("home").mkdir("user1")
        filename = str(user_root.join("my_file.txt"))
        with open(filename, "w") as f_out:
            f_out.write("Hello World!")
        artifact = Artifact.objects.create(directory=directory, path=filename, is_permanent=True)

        assert artifact.path.size == 12
        assert str(artifact) == filename

        assert artifact.is_visible_to(users["u"][0]) == True
        assert artifact.is_visible_to(users["u"][1]) == False
        assert artifact.is_visible_to(users["u"][2]) == False

        assert artifact.get_absolute_url() == "/artifacts/%s" % filename


class TestShare(object):
    def test_str_and_url(self, users, settings, tmpdir):
        media = tmpdir.mkdir("media")
        settings.MEDIA_ROOT = str(media)
        directory = Directory.objects.create(path="/home/user1", user=users["u"][0])
        user_root = media.mkdir("home").mkdir("user1")
        filename = str(user_root.join("my_file.txt"))
        with open(filename, "w") as f_out:
            f_out.write("Hello World!")
        artifact = Artifact.objects.create(directory=directory, path=filename)
        share = Share.objects.create(artifact=artifact, user=users["u"][0])

        assert str(share) == "%s -> %s" % (share.token, filename)
        assert share.get_absolute_url() == "/shares/%s" % bytes2unicode(share.token)
