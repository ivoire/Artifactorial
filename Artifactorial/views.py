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
from django.forms import ModelForm
from django.http import (
  FileResponse,
  Http404,
  HttpResponse,
  HttpResponseBadRequest,
  HttpResponseForbidden,
  HttpResponseNotAllowed,
  QueryDict
)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from Artifactorial.models import AuthToken, Artifact, Directory, Share

import base64
import hashlib
import mimetypes
import os


class ArtifactForm(ModelForm):
    class Meta:
        model = Artifact
        fields = ('path', 'directory', 'is_permanent')


def get_current_user(request, token):
    # If the token is None, save one dummy sql request
    if token is None:
        return request.user

    # Try to match find the token
    try:
        token = AuthToken.objects.get(secret=token)
        return token.user
    except AuthToken.DoesNotExist:
        return request.user


def _get(request, filename):
    # Get the current user
    user = get_current_user(request,
                            request.GET.get('token', None))

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
        directories = Directory.objects.filter(Q(path__startswith="%s" % (dirname)) | Q(path=dirname)).select_related("user", "group")
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
        artifacts = Artifact.objects.filter(path__startswith=filename.lstrip('/')).select_related("directory")
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

        # Return the right formating (only html, json or yaml)
        formating = request.GET.get('format', 'html')
        content_types = {'html': 'text/html',
                         'json': 'application/json',
                         'yaml': 'application/yaml'}
        if formating not in ['html', 'json', 'yaml']:
            return HttpResponseBadRequest()
        return render(request, "Artifactorial/list.%s" % formating,
                      {'directory': dirname,
                       'directories': sorted(dir_set),
                       'files': sorted(art_list),
                       'token': request.GET.get('token', None)},
                      content_type=content_types[formating])

    else:
        # Serving the file
        # TODO: use django-sendfile for more performances
        artifact = get_object_or_404(Artifact, path=filename.lstrip('/'))
        if not artifact.is_visible_to(user):
            return HttpResponseForbidden()

        # Guess the mimetype
        mime = mimetypes.guess_type(artifact.path.name)
        response = FileResponse(open(artifact.path.name, 'rb'),
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
    # Remove the trailing '/' if needed
    filename = filename.rstrip('/')
    # Find the directory by name
    directory_path = '/' + filename
    directory = get_object_or_404(Directory, path=directory_path)

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
    form = ArtifactForm({'directory': directory.id,
                         'is_permanent': request.POST.get('is_permanent', False)},
                        request.FILES)
    if form.is_valid():
        artifact = form.save()
        return HttpResponse(artifact.path.url, content_type='text/plain')
    else:
        return HttpResponseBadRequest()


@csrf_exempt
def artifacts(request, filename):
    if request.method == 'GET':
        return _get(request, filename)
    elif request.method == 'HEAD':
        return _head(request, filename)
    elif request.method == 'POST':
        return _post(request, filename)
    else:
        return HttpResponseNotAllowed(['GET', 'HEAD', 'POST'])


@csrf_exempt
def shared_root(request):
    if request.method == 'PUT':
        # Create a new sharing link
        # Get the current user
        user = get_current_user(request,
                                request.GET.get('token', ''))
        # Grab the requested file and check permissions
        put = QueryDict(request.body)
        filename = put.get('path', '')
        artifact = get_object_or_404(Artifact, path=filename.lstrip('/'))
        if not artifact.is_visible_to(user):
            return HttpResponseForbidden()

        # Create the link
        share = Share(artifact=artifact)
        share.save()
        return HttpResponse(share.token, content_type='text/plain')
    else:
        return HttpResponseNotAllowed(['PUT'])


def shared(request, token):
    share = get_object_or_404(Share, token=token)
    artifact = share.artifact

    # Guess the mimetype
    mime = mimetypes.guess_type(artifact.path.name)
    response = FileResponse(open(artifact.path.name, 'rb'),
                            content_type=mime[0] if mime[0]
                            else 'text/plain')

    response['Content-Length'] = artifact.path.size
    return response

