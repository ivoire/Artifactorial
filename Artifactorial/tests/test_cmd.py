# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2017-present Linaro Limited
#
# Author: Rémi Duraffort <remi.duraffort@linaro.org>
#
# SPDX-License-Identifier: MIT

from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.management import call_command

from Artifactorial.models import Artifact, Directory

from datetime import timedelta
import os
import pytest
import sys


@pytest.fixture
def users(db):
    group1 = Group.objects.create(name="grp1")
    group2 = Group.objects.create(name="grp2")
    user1 = User.objects.create_user("user1", "user1@example.com", "123456")
    user1.groups.add(group1, group2)
    user2 = User.objects.create_user("user2", "user2@example.com", "123456")
    user2.groups.add(group1)
    user3 = User.objects.create_user("user3", "user3@example.com", "123456")

    return {"u": [user1, user2, user3], "g": [group1, group2]}


class TestClean(object):
    def test_clean(self, users, settings, tmpdir):
        media = tmpdir.mkdir("media")
        settings.MEDIA_ROOT = str(media)
        dir1 = Directory.objects.create(path="/home/user1", user=users["u"][0])
        dir2 = Directory.objects.create(path="/home/user2", user=users["u"][1])
        user1_root = media.mkdir("home").mkdir("user1")
        user2_root = media.join("home").mkdir("user2")

        user1_arts = []
        for (index, f_name) in enumerate(["file1.txt", "testing.py", "hello.jpg"]):
            filename = str(user1_root.join(f_name))
            with open(filename, "wb") as f_out:
                f_out.write(os.urandom(32))
            art = Artifact.objects.create(directory=dir1, path=filename)
            art.created_at -= timedelta(days=index)
            art.save()
            user1_arts.append(art)
        user2_arts = []
        for (index, f_name) in enumerate(["file2.txt", "bla.py", "world.pdf"]):
            filename = str(user2_root.join(f_name))
            with open(filename, "wb") as f_out:
                f_out.write(os.urandom(32))
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
        call_command("clean")
        assert dir1.artifact_set.count() == 3
        assert dir2.artifact_set.count() == 3

        dir1.ttl = 2
        dir1.save()
        call_command("clean")
        assert dir1.artifact_set.count() == 2
        assert os.path.exists(user1_arts[0].path.path) == True
        assert os.path.exists(user1_arts[1].path.path) == True
        assert os.path.exists(user1_arts[2].path.path) == False
        assert dir2.artifact_set.count() == 3
        assert os.path.exists(user2_arts[0].path.path) == True
        assert os.path.exists(user2_arts[1].path.path) == True
        assert os.path.exists(user2_arts[2].path.path) == True

        call_command("clean", ttl=2)
        assert dir2.artifact_set.count() == 2
        assert os.path.exists(user2_arts[0].path.path) == True
        assert os.path.exists(user2_arts[1].path.path) == True
        assert os.path.exists(user2_arts[2].path.path) == False

        # Set a 0 TTL => do not remove anything (unless permanent is True)
        call_command("clean", ttl=0)
        assert dir1.artifact_set.count() == 2
        assert os.path.exists(user1_arts[0].path.path) == True
        assert os.path.exists(user1_arts[1].path.path) == True
        assert os.path.exists(user1_arts[2].path.path) == False
        assert dir2.artifact_set.count() == 2
        assert os.path.exists(user2_arts[0].path.path) == True
        assert os.path.exists(user2_arts[1].path.path) == True
        assert os.path.exists(user2_arts[2].path.path) == False

        call_command("clean", purge=True, ttl=0)
        assert dir1.artifact_set.count() == 0
        assert os.path.exists(user1_arts[0].path.path) == False
        assert os.path.exists(user1_arts[1].path.path) == False
        assert os.path.exists(user1_arts[2].path.path) == False
        assert dir2.artifact_set.count() == 0
        assert os.path.exists(user2_arts[0].path.path) == False
        assert os.path.exists(user2_arts[1].path.path) == False
        assert os.path.exists(user2_arts[2].path.path) == False
