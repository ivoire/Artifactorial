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

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from Artifactorial.models import Directory, AuthToken

class BasicTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_empty(self):
        response = self.client.get(reverse('root', args=['']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], [])
        self.assertEqual(ctx['files'], [])

        response = self.client.get(reverse('root', args=['pub']))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('root', args=['test']))
        self.assertEqual(response.status_code, 404)

    def test_head_empty(self):
        response = self.client.head(reverse('root', args=['']))
        self.assertEqual(response.status_code, 404)

        response = self.client.head(reverse('root', args=['pub']))
        self.assertEqual(response.status_code, 404)

    def test_post_empty(self):
        response = self.client.post(reverse('root', args=['']), data={})
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse('root', args=['pub']), data={})
        self.assertEqual(response.status_code, 404)

    def test_others(self):
        response = self.client.put(reverse('root', args=['']))
        self.assertEqual(response.status_code, 405)
        response = self.client.delete(reverse('root', args=['']))
        self.assertEqual(response.status_code, 405)
        response = self.client.options(reverse('root', args=['']))
        self.assertEqual(response.status_code, 405)
        response = self.client.patch(reverse('root', args=['']))
        self.assertEqual(response.status_code, 405)


class GETTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user('azertyuiop',
                                              'django.test@project.org',
                                              '12789azertyuiop')
        self.user2 = User.objects.create_user('azertyuiop2',
                                              'django.test@project.org',
                                              '12789azertyuiop')

        self.token1 = AuthToken.objects.create(user=self.user1)
        self.token1bis = AuthToken.objects.create(user=self.user1)
        self.token2 = AuthToken.objects.create(user=self.user2)

        self.directories = {}
        self.directories['/pub'] = Directory.objects.create(path='/pub', user=self.user1, is_public=True)
        self.directories['/pub/debian'] = Directory.objects.create(path='/pub/debian', user=self.user1, is_public=True)
        self.directories['/private/user1'] = Directory.objects.create(path='/private/user1', user=self.user1, is_public=False)
        self.directories['/private/user2'] = Directory.objects.create(path='/private/user2', user=self.user2, is_public=False)

    def test_directories(self):
        response = self.client.get(reverse('root', args=['']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], ['pub'])
        self.assertEqual(ctx['files'], [])

        response = self.client.get(reverse('root', args=['pub/']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/pub')
        self.assertEqual(ctx['directories'], ['debian'])
        self.assertEqual(ctx['files'], [])

        response = self.client.get(reverse('root', args=['pub/debian/']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/pub/debian')
        self.assertEqual(ctx['directories'], [])
        self.assertEqual(ctx['files'], [])

        # Check that we don't see anything in the private directory
        response = self.client.get(reverse('root', args=['private/']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/private')
        self.assertEqual(ctx['directories'], [])
        self.assertEqual(ctx['files'], [])

        response = self.client.get("%s?token=%s" % (reverse('root', args=['private/']),
                                                    self.token1.secret))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/private')
        self.assertEqual(ctx['directories'], ['user1'])
        self.assertEqual(ctx['files'], [])

        response = self.client.get("%s?token=%s" % (reverse('root', args=['private/']),
                                                    self.token1bis.secret))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/private')
        self.assertEqual(ctx['directories'], ['user1'])
        self.assertEqual(ctx['files'], [])

        response = self.client.get("%s?token=%s" % (reverse('root', args=['private/']),
                                                    self.token2.secret))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/private')
        self.assertEqual(ctx['directories'], ['user2'])
        self.assertEqual(ctx['files'], [])
