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

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.test import TestCase
from django.test.client import Client

from Artifactorial.models import Artifact, Directory, AuthToken

import os


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
        self.directories['/pub/debian'] = Directory.objects.create(path='/pub/debian',
                                                                   user=self.user1,
                                                                   is_public=True)
        self.directories['/private/user1'] = Directory.objects.create(path='/private/user1',
                                                                      user=self.user1,
                                                                      is_public=False)
        self.directories['/private/user2'] = Directory.objects.create(path='/private/user2',
                                                                      user=self.user2,
                                                                      is_public=False)
        self.directories['/private/group'] = Directory.objects.create(path='/private/group',
                                                                      group=self.group,
                                                                      is_public=False)
        self.directories['/anonymous'] = Directory.objects.create(path='/anonymous',
                                                                  is_public=False)

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
        self.assertEqual(ctx['files'], [])

        q.update({'token': self.token3.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], ['anonymous', 'private', 'pub'])
        self.assertEqual(ctx['files'], [])

        # Invalid users should not be able to access private nor anonymous directories
        q.update({'token': self.token4.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], ['pub'])
        self.assertEqual(ctx['files'], [])

    def test_public_file_access(self):
        # Create public files
        a1 = Artifact.objects.create(path='pub/debian/2015/01/debian-6.iso',
                                     directory=self.directories['/pub/debian'])
        a2 = Artifact.objects.create(path='pub/debian/2015/01/debian-7.iso',
                                     directory=self.directories['/pub/debian'])
        a3 = Artifact.objects.create(path='pub/debian/2015/01/debian-sid.iso',
                                     directory=self.directories['/pub/debian'])
        a4 = Artifact.objects.create(path='pub/debian/2015/02/debian-sid2.iso',
                                     directory=self.directories['/pub/debian'])
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'pub', 'debian', '2015', '01'))
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'pub', 'debian', '2015', '02'))
        with open(os.path.join(settings.MEDIA_ROOT, a1.path.name), 'wb') as f_out:
            f_out.write(b'debian 6 iso')
        with open(os.path.join(settings.MEDIA_ROOT, a2.path.name), 'wb') as f_out:
            f_out.write(b'debian 7 iso is better')
        with open(os.path.join(settings.MEDIA_ROOT, a3.path.name), 'wb') as f_out:
            f_out.write(b'debian sid is way better')
        with open(os.path.join(settings.MEDIA_ROOT, a4.path.name), 'wb') as f_out:
            f_out.write(b'debian sid is way better')

        # Test directory listing
        response = self.client.get(reverse('root', args=['pub/debian/']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/pub/debian')
        self.assertEqual(ctx['directories'], ['2015'])
        self.assertEqual(ctx['files'], [])

        response = self.client.get(reverse('root', args=['pub/debian/2015/']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/pub/debian/2015')
        self.assertEqual(ctx['directories'], ['01', '02'])
        self.assertEqual(ctx['files'], [])

        response = self.client.get(reverse('root', args=['pub/debian/2015/01/']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/pub/debian/2015/01')
        self.assertEqual(ctx['directories'], [])
        self.assertEqual(ctx['files'], [('debian-6.iso', 12),
                                        ('debian-7.iso', 22),
                                        ('debian-sid.iso', 24)])

        response = self.client.get(reverse('root', args=['pub/debian/2015/02/']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/pub/debian/2015/02')
        self.assertEqual(ctx['directories'], [])
        self.assertEqual(ctx['files'], [('debian-sid2.iso', 24)])

        # Test public file access
        response = self.client.get(reverse('root', args=['pub/debian/2015/01/debian-6.iso']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'debian 6 iso'])
        self.assertEqual(response['Content-Length'], '12')
        self.assertEqual(response['Content-Type'], 'application/x-iso9660-image')

        response = self.client.get(reverse('root', args=['pub/debian/2015/01/debian-7.iso']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'debian 7 iso is better'])
        self.assertEqual(response['Content-Length'], '22')
        self.assertEqual(response['Content-Type'], 'application/x-iso9660-image')

        response = self.client.get(reverse('root', args=['pub/debian/2015/02/debian-sid2.iso']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'debian sid is way better'])
        self.assertEqual(response['Content-Length'], '24')
        self.assertEqual(response['Content-Type'], 'application/x-iso9660-image')

    def test_private_file_access(self):
        # Create private files
        a1 = Artifact.objects.create(path='private/user1/my-cv.pdf',
                                     directory=self.directories['/private/user1'])
        a2 = Artifact.objects.create(path='private/user2/foo.jpg',
                                     directory=self.directories['/private/user2'])
        a3 = Artifact.objects.create(path='private/group/foo/bar.doc',
                                     directory=self.directories['/private/group'])
        a4 = Artifact.objects.create(path='anonymous/a/b.c',
                                     directory=self.directories['/anonymous'])
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'private', 'user1'))
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'private', 'user2'))
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'private', 'group', 'foo'))
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'anonymous', 'a'))
        with open(os.path.join(settings.MEDIA_ROOT, a1.path.name), 'wb') as f_out:
            f_out.write(b'I\'m awsome')
        with open(os.path.join(settings.MEDIA_ROOT, a2.path.name), 'wb') as f_out:
            f_out.write(b'Nice picture')
        with open(os.path.join(settings.MEDIA_ROOT, a3.path.name), 'wb') as f_out:
            f_out.write(b'One empty doc')
        with open(os.path.join(settings.MEDIA_ROOT, a4.path.name), 'wb') as f_out:
            f_out.write(b'int main(){return 0;}')

        # Test that anonymous users can't have access
        response = self.client.get(reverse('root', args=['private/user1/my-cv.pdf']))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('root', args=['private/user2/foo.jpg']))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('root', args=['private/group/foo/bar.doc']))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('root', args=['anonymous/a/b.c']))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('root', args=['anonymous/a/b.cpp']))
        self.assertEqual(response.status_code, 404)

        # Test owner access
        q = QueryDict('', mutable=True)

        q.update({'token': self.token1.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['private/user1/my-cv.pdf']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'I\'m awsome'])
        self.assertEqual(response['Content-Length'], '10')
        self.assertEqual(response['Content-Type'], 'application/pdf')

        q.update({'token': self.token1bis.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['private/user1/my-cv.pdf']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'I\'m awsome'])
        self.assertEqual(response['Content-Length'], '10')
        self.assertEqual(response['Content-Type'], 'application/pdf')

        q.update({'token': self.token2.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['private/user1/my-cv.pdf']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 403)
        response = self.client.get("%s?%s" % (reverse('root', args=['private/user2/foo.jpg']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'Nice picture'])
        self.assertEqual(response['Content-Length'], '12')
        self.assertEqual(response['Content-Type'], 'image/jpeg')

        # Test private group access
        q.update({'token': self.token2.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['private/group/foo/bar.doc']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'One empty doc'])
        self.assertEqual(response['Content-Length'], '13')
        self.assertEqual(response['Content-Type'], 'application/msword')

        q.update({'token': self.token3.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['private/group/foo/bar.doc']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'One empty doc'])
        self.assertEqual(response['Content-Length'], '13')
        self.assertEqual(response['Content-Type'], 'application/msword')

        # Test anonymous access
        q.update({'token': self.token1.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['anonymous/a/b.c']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'int main(){return 0;}'])
        self.assertEqual(response['Content-Length'], '21')
        self.assertEqual(response['Content-Type'], 'text/x-csrc')

        q.update({'token': self.token2.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['anonymous/a/b.c']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'int main(){return 0;}'])
        self.assertEqual(response['Content-Length'], '21')
        self.assertEqual(response['Content-Type'], 'text/x-csrc')

        q.update({'token': self.token3.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['anonymous/a/b.c']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.streaming_content), [b'int main(){return 0;}'])
        self.assertEqual(response['Content-Length'], '21')
        self.assertEqual(response['Content-Type'], 'text/x-csrc')

        # Test inactive user access
        q.update({'token': self.token4.secret})
        response = self.client.get("%s?%s" % (reverse('root', args=['anonymous/a/b.c']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 403)
        response = self.client.get("%s?%s" % (reverse('root', args=['private/user2/foo.jpg']),
                                              q.urlencode()))
        self.assertEqual(response.status_code, 403)


class ModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('azertyuiop',
                                              'django.test@project.org',
                                              '12789azertyuiop')
        self.group = Group.objects.create(name='user 1')
        self.group.user_set.add(self.user1)
        self.group.save()

        self.dir1 = Directory.objects.create(path='/pub', user=self.user1, is_public=True)
        self.dir2 = Directory.objects.create(path='/pub/groups', group=self.group, is_public=True)
        self.dir3 = Directory.objects.create(path='/private', is_public=True)

    def test_directories_string(self):
        self.assertEqual(str(self.dir1), "%s (%s)" % ('/pub', self.user1.get_full_name()))
        self.assertEqual(str(self.dir2), "%s (%s)" % ('/pub/groups', self.group))
        self.assertEqual(str(self.dir3), "%s (anonymous)" % ('/private'))

    def test_directory_clean(self):
        self.dir1.clean()
        self.dir2.clean()
        self.dir3.clean()

        d_in = Directory.objects.create(path='/invalid', user=self.user1, group=self.group)
        self.assertRaises(ValidationError, d_in.clean)
        d_in = Directory.objects.create(path='/in/../valid/', user=self.user1)
        self.assertRaises(ValidationError, d_in.clean)
        d_in = Directory.objects.create(path='/invalid/', user=self.user1)
        self.assertRaises(ValidationError, d_in.clean)
        d_in = Directory.objects.create(path='invalid', user=self.user1)
        self.assertRaises(ValidationError, d_in.clean)
