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

from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.http import QueryDict
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
        self.user3 = User.objects.create_user('plop',
                                              'plop@project.org',
                                              'plop')
        self.user4 = User.objects.create_user('foo',
                                              'bar@project.org',
                                              'bar')
        self.user4.is_active = False
        self.user4.save()
        self.group = Group.objects.create(name='user 2 and3')
        self.group.user_set.add(self.user2)
        self.group.user_set.add(self.user3)
        self.group.save()

        self.token1 = AuthToken.objects.create(user=self.user1)
        self.token1bis = AuthToken.objects.create(user=self.user1)
        self.token2 = AuthToken.objects.create(user=self.user2)
        self.token3 = AuthToken.objects.create(user=self.user3)
        self.token4 = AuthToken.objects.create(user=self.user4)

        self.directories = {}
        self.directories['/pub'] = Directory.objects.create(path='/pub', user=self.user1, is_public=True)
        self.directories['/pub/debian'] = Directory.objects.create(path='/pub/debian', user=self.user1, is_public=True)
        self.directories['/private/user1'] = Directory.objects.create(path='/private/user1', user=self.user1, is_public=False)
        self.directories['/private/user2'] = Directory.objects.create(path='/private/user2', user=self.user2, is_public=False)
        self.directories['/private/group'] = Directory.objects.create(path='/private/group', group=self.group, is_public=False)
        self.directories['/anonymous'] = Directory.objects.create(path='/anonymous', is_public=False)

    def test_pub_directories(self):
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

    def test_private_directories(self):
        q = QueryDict('', mutable=True)
        q.update({'token': self.token1.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['private/']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/private')
        self.assertEqual(ctx['directories'], ['user1'])
        self.assertEqual(ctx['files'], [])

        q.update({'token': self.token1bis.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['private/']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/private')
        self.assertEqual(ctx['directories'], ['user1'])
        self.assertEqual(ctx['files'], [])

        q.update({'token': self.token2.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['private/']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/private')
        self.assertEqual(ctx['directories'], ['group', 'user2'])
        self.assertEqual(ctx['files'], [])

        q.update({'token': self.token3.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['private/']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/private')
        self.assertEqual(ctx['directories'], ['group'])
        self.assertEqual(ctx['files'], [])

    def test_anonymous_directories(self):
        response = self.client.get(reverse('root', args=['']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], ['pub'])
        self.assertEqual(ctx['files'], [])

        q = QueryDict('', mutable=True)
        q.update({'token': self.token1.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], ['anonymous', 'private', 'pub'])
        self.assertEqual(ctx['files'], [])

        q.update({'token': self.token2.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], ['anonymous', 'private', 'pub'])

        q.update({'token': self.token3.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], ['anonymous', 'private', 'pub'])

        # Invalid users should not be able to access private nor anonymous directories
        q.update({'token': self.token4.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], ['pub'])
