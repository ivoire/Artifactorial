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

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client


class GETTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_empty(self):
        response = self.client.get(reverse('root', args=['']))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx['directory'], '/')
        self.assertEqual(ctx['directories'], [])
        self.assertEqual(ctx['files'], [])

        response = self.client.get(reverse('root', args=['/pub']))
        self.assertEqual(response.status_code, 404)
