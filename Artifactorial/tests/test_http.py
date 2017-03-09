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
from django.core.management import call_command
from django.core.urlresolvers import reverse

from Artifactorial.models import Artifact, AuthToken, Directory

import base64
import binascii
from datetime import timedelta
import os
import pytest
import re
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


class TestHTTPCode(object):
    def test_empty_get(self, client, db):
        response = client.get(reverse('home'))
        assert response.status_code == 200

        response = client.get(reverse('artifacts', args=['']))
        assert response.status_code == 200

        response = client.get(reverse('artifacts', args=['pub/']))
        assert response.status_code == 404

        response = client.get(reverse('artifacts', args=['test']))
        assert response.status_code == 404

    def test_empty_head(self, client, db):
        response = client.head(reverse('artifacts', args=['']))
        assert response.status_code == 404

        response = client.head(reverse('artifacts', args=['pub']))
        assert response.status_code == 404

    def test_empty_posts(self, client, db):
        response = client.post(reverse('artifacts', args=['']), data={})
        assert response.status_code == 404

        response = client.post(reverse('artifacts', args=['pub']), data={})
        assert response.status_code == 404

    def test_others_verbs_on_artifacts(self, client, db):
        response = client.put(reverse('artifacts', args=['']))
        assert response.status_code == 405
        response = client.delete(reverse('artifacts', args=['']))
        assert response.status_code == 405
        response = client.options(reverse('artifacts', args=['']))
        assert response.status_code == 405
        response = client.patch(reverse('artifacts', args=['']))
        assert response.status_code == 405

    def test_invalid_formating(self, client, db):
        response = client.get("%s?format=html" % reverse('artifacts', args=['']))
        assert response.status_code == 200
        response = client.get("%s?format=json" % reverse('artifacts', args=['']))
        assert response.status_code == 200
        response = client.get("%s?format=yaml" % reverse('artifacts', args=['']))
        assert response.status_code == 200
        response = client.get("%s?format=cvs" % reverse('artifacts', args=['']))
        assert response.status_code == 400

    def test_verbs_on_shares_root(self, client, db):
        response = client.put(reverse('shares.root'))
        assert response.status_code == 404
        response = client.get(reverse('shares.root'))
        assert response.status_code == 405
        response = client.delete(reverse('shares.root'))
        assert response.status_code == 405


class TestDirectories(object):
    def test_empty(self, client, db):
        response = client.get(reverse("directories.index"))
        assert response.status_code == 200
        assert response.context["directories"] == []

    def test_anonymous(self, client, db, users):
        Directory.objects.create(path="/home/user1", user=users["u"][0], is_public=True)
        Directory.objects.create(path="/home/user2", user=users["u"][1], is_public=True)
        Directory.objects.create(path="/home/user3", user=users["u"][2], is_public=False)

        response = client.get(reverse("directories.index"))
        assert response.status_code == 200
        assert len(response.context["directories"]) == 2
        assert response.context["directories"][0][0].path == "/home/user1"
        assert response.context["directories"][0][1] == False
        assert response.context["directories"][1][0].path == "/home/user2"
        assert response.context["directories"][1][1] == False

    def test_user1(self, client, db, users):
        Directory.objects.create(path="/home/user1", user=users["u"][0], is_public=True)
        Directory.objects.create(path="/home/user2", user=users["u"][1], is_public=True)
        Directory.objects.create(path="/home/user3", user=users["u"][2], is_public=False)
        token = AuthToken.objects.create(user=users["u"][0])

        response = client.get("%s?token=%s" % (reverse("directories.index"), bytes2unicode(token.secret)))
        assert response.status_code == 200
        assert len(response.context["directories"]) == 2
        assert response.context["directories"][0][0].path == "/home/user1"
        assert response.context["directories"][0][1] == True
        assert response.context["directories"][1][0].path == "/home/user2"
        assert response.context["directories"][1][1] == False

    def test_user3(self, client, db, users):
        Directory.objects.create(path="/home/user1", user=users["u"][0], is_public=True)
        Directory.objects.create(path="/home/user2", user=users["u"][1], is_public=True)
        Directory.objects.create(path="/home/user3", user=users["u"][2], is_public=False)
        token = AuthToken.objects.create(user=users["u"][2])

        response = client.get("%s?token=%s" % (reverse("directories.index"), bytes2unicode(token.secret)))
        assert response.status_code == 200
        assert len(response.context["directories"]) == 3
        assert response.context["directories"][0][0].path == "/home/user1"
        assert response.context["directories"][0][1] == False
        assert response.context["directories"][1][0].path == "/home/user2"
        assert response.context["directories"][1][1] == False
        assert response.context["directories"][2][0].path == "/home/user3"
        assert response.context["directories"][2][1] == True


class TestShares(object):
    def test_put(self, client, db, settings, tmpdir, users):
        media = tmpdir.mkdir("media")
        settings.MEDIA_ROOT = str(media)

        filename = str(media.mkdir("home").mkdir("user1").join("bla.txt"))
        with open(filename, "w") as f_out:
            f_out.write("something")

        dir1 = Directory.objects.create(path="/home/user1", user=users["u"][0], is_public=True)
        art1 = Artifact.objects.create(path="home/user1/bla.txt", directory=dir1)
        token = AuthToken.objects.create(user=users["u"][0])

        # Create a share for our own artifact
        response = client.put(reverse("shares.root"), data="path=/home/user1/bla.txt&token=%s" % bytes2unicode(token.secret))
        assert response.status_code == 200
        pattern = re.compile("http://testserver/shares/([a-f0-9]+)$")
        assert pattern.match(bytes2unicode(response.content))

        # Create a share for a readable artifact
        token = AuthToken.objects.create(user=users["u"][1])
        response = client.put(reverse("shares.root"), data="path=/home/user1/bla.txt&token=%s" % bytes2unicode(token.secret))
        assert response.status_code == 200
        match = pattern.match(bytes2unicode(response.content))
        assert match

        response = client.get(reverse("shares", args=[match.groups()[0]]))
        assert response.status_code == 200
        resp = list(response.streaming_content)
        assert len(resp) == 1
        assert bytes2unicode(resp[0]) == "something"
        assert response["Content-Type"] == "text/plain"
        assert response["Content-Length"] == "9"


    def test_invalid_put(self, client, db, users):
        # Only PUT is allowed yet
        assert client.get(reverse("shares.root")).status_code == 405

        dir1 = Directory.objects.create(path="/home/user1", user=users["u"][0])
        art1 = Artifact.objects.create(path="home/user1/bla.txt", directory=dir1)
        token = AuthToken.objects.create(user=users["u"][1])

        # dir1 is not public
        response = client.put(reverse("shares.root"), data="path=/home/user1/bla.txt&token=%s" % bytes2unicode(token.secret))
        assert response.status_code == 403

        # Make dir1 public and try with an anonymous user
        dir1.is_public = True
        dir1.save()
        response = client.put(reverse("shares.root"), data="path=/home/user1/bla.txt")
        assert response.status_code == 403


class TestTokens(object):
    def test_anonymous_list(self, client):
        # Redirection to the authentication page
        response = client.get(reverse("tokens.index"))
        assert response.status_code == 302
        assert response["location"] == "/accounts/login/?next=/tokens/"

    def test_listing(self, client, users):
        assert client.login(username=users["u"][0], password="123456")
        response = client.get(reverse("tokens.index"))
        assert response.status_code == 200
        assert len(response.context["tokens"]) == 0

        # Add some tokens using the ORM
        t1 = AuthToken.objects.create(user=users["u"][0])
        t2 = AuthToken.objects.create(user=users["u"][1])
        t3 = AuthToken.objects.create(user=users["u"][2])
        t4 = AuthToken.objects.create(user=users["u"][0], description="Hello")
        response = client.get(reverse("tokens.index"))
        assert response.status_code == 200
        assert len(response.context["tokens"]) == 2
        assert response.context["tokens"][0] == t1
        assert response.context["tokens"][1] == t4

        assert client.login(username=users["u"][1], password="123456")
        response = client.get(reverse("tokens.index"))
        assert response.status_code == 200
        assert len(response.context["tokens"]) == 1
        assert response.context["tokens"][0] == t2

    def test_posting(self, client, users):
        assert client.login(username=users["u"][0], password="123456")
        response = client.get(reverse("tokens.index"))
        assert response.status_code == 200
        assert len(response.context["tokens"]) == 0

        response = client.post(reverse("tokens.index"))
        assert response.status_code == 200
        assert len(response.context["tokens"]) == 1
        assert response.context["tokens"][0] == AuthToken.objects.get(user=users["u"][0])

        response = client.post(reverse("tokens.index"), data={"description": "Hello world"})
        assert response.status_code == 200
        assert len(response.context["tokens"]) == 2
        assert response.context["tokens"][0] == AuthToken.objects.get(user=users["u"][0], description='')
        assert response.context["tokens"][1] == AuthToken.objects.get(user=users["u"][0], description="Hello world")

    def test_failing_delete(self, client, users):
        response = client.get(reverse("tokens.delete", args=["0"]))
        assert response.status_code == 302
        assert response["location"] == "/accounts/login/?next=/tokens/0/delete/"

        assert client.login(username=users["u"][0], password="123456")
        response = client.get(reverse("tokens.delete", args=["0"]))
        assert response.status_code == 404

    def test_delete(self, client, users):
        t1 = AuthToken.objects.create(user=users["u"][0])
        t2 = AuthToken.objects.create(user=users["u"][1])
        t3 = AuthToken.objects.create(user=users["u"][2])
        t4 = AuthToken.objects.create(user=users["u"][0], description="Hello")

        response = client.get(reverse("tokens.delete", args=["0"]))
        assert response.status_code == 302
        assert response["location"] == "/accounts/login/?next=/tokens/0/delete/"

        assert client.login(username=users["u"][0], password="123456")
        response = client.get(reverse("tokens.delete", args=[t1.id]))
        assert response.status_code == 302
        assert response["location"] == reverse("tokens.index")
        assert AuthToken.objects.get(user=users["u"][0]) == t4

        # Forbidden to remove other users token
        response = client.get(reverse("tokens.delete", args=[t2.id]))
        assert response.status_code == 404

        # Remove the last one we have
        assert client.login(username=users["u"][0], password="123456")
        response = client.get(reverse("tokens.delete", args=[t4.id]))
        assert response.status_code == 302
        assert response["location"] == reverse("tokens.index")
        assert len(AuthToken.objects.filter(user=users["u"][0])) == 0
        assert AuthToken.objects.get(user=users["u"][1]) == t2
        assert AuthToken.objects.get(user=users["u"][2]) == t3


class TestPostingArtifacts(object):
    def test_push_non_existent_directory(self, client, settings, tmpdir, users):
        media = tmpdir.mkdir("media")
        settings.MEDIA_ROOT = str(media)
        Directory.objects.create(path="/home/user1", user=users["u"][0])

        # Not existing directory
        response = client.post(reverse("artifacts", args=["home/user"]))
        assert response.status_code == 404
        # Not allowed to write to it
        response = client.post(reverse("artifacts", args=["home/user1"]))
        assert response.status_code == 403

        assert client.login(username=users["u"][1], password="123456")
        response = client.post(reverse("artifacts", args=["home/user1"]))
        assert response.status_code == 403

    def test_quota(self, client, settings, tmpdir, users):
        media = tmpdir.mkdir("media")
        filename = str(tmpdir.join("data.txt"))
        with open(filename, "w") as f_out:
            f_out.write("Hello World!!!")
        settings.MEDIA_ROOT = str(media)
        d = Directory.objects.create(path="/home/user1", user=users["u"][0])

        assert client.login(username=users["u"][0], password="123456")
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["home/user1"]),
                                   data={"path": f_in})
        assert response.status_code == 200
        content = bytes2unicode(response.content)
        assert content.startswith("home/user1/")
        assert content.endswith("data.txt")

        # Change the quota and try to add another file
        d.quota = 27
        d.save()
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["home/user1"]),
                                   data={"path": f_in})
        assert response.status_code == 403

        # Fill completely the directory
        d.quota = 28
        d.save()
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["home/user1"]),
                                   data={"path": f_in})
        assert response.status_code == 200

    def test_group_write(self, client, settings, tmpdir, users):
        media = tmpdir.mkdir("media")
        filename = str(tmpdir.join("data.txt"))
        with open(filename, "w") as f_out:
            f_out.write("Hello World!!!")
        settings.MEDIA_ROOT = str(media)
        d = Directory.objects.create(path="/home/user1", group=users["g"][0])

        # Same group
        assert client.login(username=users["u"][0], password="123456")
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["home/user1"]),
                                   data={"path": f_in})
        assert response.status_code == 200

        # Same group
        assert client.login(username=users["u"][1], password="123456")
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["home/user1"]),
                                   data={"path": f_in})
        assert response.status_code == 200

        # Another group
        assert client.login(username=users["u"][2], password="123456")
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["home/user1"]),
                                   data={"path": f_in})
        assert response.status_code == 403

        # Anonymous user
        client.logout()
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["home/user1"]),
                                   data={"path": f_in})
        assert response.status_code == 403

    def test_anonymous_directories(self, client, settings, tmpdir, users):
        media = tmpdir.mkdir("media")
        filename = str(tmpdir.join("something.txt"))
        with open(filename, "w") as f_out:
            f_out.write("Hello World!!!")
        settings.MEDIA_ROOT = str(media)
        d = Directory.objects.create(path="/pub")

        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["pub/"]),
                                   data={"path": f_in})
        assert response.status_code == 200

        assert client.login(username=users["u"][0], password="123456")
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["pub/"]),
                                   data={"path": f_in})
        assert response.status_code == 200

    def test_invalid_request(self, client, settings, tmpdir, users):
        media = tmpdir.mkdir("media")
        filename = str(tmpdir.join("data.txt"))
        with open(filename, "w") as f_out:
            f_out.write("Hello World!!!")
        settings.MEDIA_ROOT = str(media)
        d = Directory.objects.create(path="/home/user1", user=users["u"][0])

        # Do not send a path
        assert client.login(username=users["u"][0], password="123456")
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["home/user1"]),
                                   data={})
        assert response.status_code == 400

    def test_intricated_directories(self, client, settings, tmpdir, users):
        # /pub and /pub/debian => write to /pub or /pub/Debian
        media = tmpdir.mkdir("media")
        filename = str(tmpdir.join("data.txt"))
        with open(filename, "w") as f_out:
            f_out.write("Hello World!!!")
        settings.MEDIA_ROOT = str(media)
        d1 = Directory.objects.create(path="/pub")
        d2 = Directory.objects.create(path="/pub/debian", user=users["u"][0])

        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["pub"]),
                                   data={"path": f_in})
        assert response.status_code == 200
        content = bytes2unicode(response.content)
        assert content.startswith("pub/")
        assert not content.startswith("pub/debian")

        assert client.login(username=users["u"][0], password="123456")
        with open(filename, "r") as f_in:
            response = client.post(reverse("artifacts", args=["pub/debian"]),
                                   data={"path": f_in})
        assert response.status_code == 200
        content = bytes2unicode(response.content)
        assert content.startswith("pub/debian")

        assert d1.artifact_set.all().count() == 1
        assert d2.artifact_set.all().count() == 1


class TestHead(object):
    def test_public_artifact(self, client, settings, tmpdir, users):
        media = tmpdir.mkdir("media")
        filename = str(media.mkdir("pub").mkdir("debian").join("take_my_sum.txt"))
        with open(filename, "w") as f_out:
            f_out.write("some sort of test data")
        settings.MEDIA_ROOT = str(media)
        d = Directory.objects.create(path="/pub/debian", is_public=True)
        art1 = Artifact.objects.create(path="pub/debian/take_my_sum.txt", directory=d)

        response = client.head(reverse("artifacts", args=["pub/debian/take_my_sum.txt"]))
        assert response.status_code == 200
        assert bytes2unicode(base64.b64decode(response["Content-MD5"])) == "600ae9d6304b5d939e3dc10191536c58"

        assert client.login(username=users["u"][0], password="123456")
        response = client.head(reverse("artifacts", args=["pub/debian/take_my_sum.txt"]))
        assert response.status_code == 200
        assert bytes2unicode(base64.b64decode(response["Content-MD5"])) == "600ae9d6304b5d939e3dc10191536c58"

    def test_private_artifact(self, client, settings, tmpdir, users):
        media = tmpdir.mkdir("media")
        filename = str(media.mkdir("pub").mkdir("debian").join("take_my_sum.txt"))
        with open(filename, "w") as f_out:
            f_out.write("some sort of test data")
        settings.MEDIA_ROOT = str(media)
        d = Directory.objects.create(path="/pub/debian", group=users["g"][0])
        art1 = Artifact.objects.create(path="pub/debian/take_my_sum.txt", directory=d)

        response = client.head(reverse("artifacts", args=["pub/debian/take_my_sum.txt"]))
        assert response.status_code == 403

        assert client.login(username=users["u"][0], password="123456")
        response = client.head(reverse("artifacts", args=["pub/debian/take_my_sum.txt"]))
        assert response.status_code == 200
        assert bytes2unicode(base64.b64decode(response["Content-MD5"])) == "600ae9d6304b5d939e3dc10191536c58"
        assert response["Content-Type"] == "text/plain"
        assert response["Content-Length"] == "22"
