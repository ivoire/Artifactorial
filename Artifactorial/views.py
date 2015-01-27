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

from django.db.models import Q
from django.core.servers.basehttp import FileWrapper
from django.forms import ModelForm
from django.http import (
  Http404,
  HttpResponse,
  HttpResponseBadRequest,
  HttpResponseForbidden,
  HttpResponseNotAllowed,
  StreamingHttpResponse
)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from Artifactorial.models import AuthToken, Artifact, Directory

import base64
import hashlib
import mimetypes
import os


class ArtifactForm(ModelForm):
    class Meta:
        model = Artifact
        fields = ('path', 'directory', 'is_permanent')


def get_current_user(request, token):
    try:
        token = AuthToken.objects.get(secret=token)
        return token.user
    except AuthToken.DoesNotExist:
        return request.user


def _get(request, filename):
    # Get the current user
    user = get_current_user(request,
                            request.GET.get('token', ''))

    # The URL regexp removes the leading slash, so add it back
    filename = '/' + filename
    # Is it a file or a path
    if filename[-1] == '/':
        dirname = os.path.dirname(filename)

        dirname_length = len(dirname)
        # Special case for the root directory
        if dirname == '/':
            dirname_length = 0

        dir_set = set()
        art_list = list()
        in_real_directory = False

        # List real directories
        directories = Directory.objects.filter(Q(path__startswith="%s" % (dirname)) | Q(path=dirname))
        for directory in directories:
            if not directory.is_visible_to(user):
                continue
            if directory.path != dirname:
                # Sub directory => print the next elements in the path
                full_dir_name = directory.path[dirname_length+1:]
                if '/' in full_dir_name:
                    dir_set.add(full_dir_name[:full_dir_name.index('/')])
                else:
                    dir_set.add(full_dir_name)
            else:
                in_real_directory = True

        # List artifacts and pseudo directories
        artifacts = Artifact.objects.filter(path__startswith=filename.lstrip('/'))
        for artifact in artifacts:
            if not artifact.is_visible_to(user):
                continue
            relative_name = artifact.path.name[dirname_length:]
            # Add pseudo directory (if the name contains a '/')
            if '/' in relative_name:
                dir_set.add(relative_name[:relative_name.index('/')])
            else:
                art_list.append((artifact.path.name[dirname_length:],
                                 artifact.path.size))

        # Raise an error if the directory does not exist
        if not dir_set and not art_list and not in_real_directory:
            raise Http404
        return render_to_response('Artifactorial/list.html',
                                  {'directory': dirname,
                                   'directories': sorted(dir_set),
                                   'files': sorted(art_list)},
                                  context_instance=RequestContext(request))
    else:
        # Serving the file
        # TODO: use django-sendfile for more performances
        artifact = get_object_or_404(Artifact, path=filename.lstrip('/'))
        if not artifact.is_visible_to(user):
            return HttpResponseForbidden()

        wrapper = FileWrapper(artifact.path.file)

        # Guess the mimetype
        mime = mimetypes.guess_type(artifact.path.name)
        response = StreamingHttpResponse(wrapper,
                                         content_type=mime[0] if mime[0]
                                         else 'text/plain')

        response['Content-Length'] = artifact.path.size
        return response


def _head(request, filename):
    user = get_current_user(request,
                            request.GET.get('token', ''))
    artifact = get_object_or_404(Artifact, path=filename.lstrip('/'))
    if not artifact.is_visible_to(user):
        return HttpResponseForbidden()

    # Build the response
    response = HttpResponse('')
    mime = mimetypes.guess_type(artifact.path.name)
    response['Content-Type'] = mime[0] if mime[0] else 'text/plain'
    response['Content-Length'] = artifact.path.size
    # Compute the MD5
    md5 = hashlib.md5()
    for chunk in artifact.path.chunks():
        md5.update(chunk)
    response['Content-MD5'] = base64.b64encode(md5.hexdigest().encode('utf-8'))

    return response


def _post(request, filename):
    # Find the directory by name
    directory_path = '/' + filename
    directory = get_object_or_404(Directory, path=directory_path)
    request.POST['directory'] = directory.id

    user = get_current_user(request,
                            request.POST.get('token', ''))

    # Is the directory writable to this user?
    if not directory.is_writable_to(user):
        return HttpResponseForbidden()

    # Check the quota
    if 'path' in request.FILES:
        if request.FILES['path'].size + directory.size() > directory.quota:
            return HttpResponseForbidden()

    # Validate the updated form
    form = ArtifactForm(request.POST, request.FILES)
    if form.is_valid():
        artifact = form.save()
        return HttpResponse(artifact.path.url, content_type='text/plain')
    else:
        return HttpResponseBadRequest()


@csrf_exempt
def root(request, filename):
    if request.method == 'GET':
        return _get(request, filename)
    elif request.method == 'HEAD':
        return _head(request, filename)
    elif request.method == 'POST':
        return _post(request, filename)
    else:
        return HttpResponseNotAllowed(['GET', 'HEAD', 'POST'])
