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
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import ModelForm
from django.http import (
  FileResponse,
  Http404,
  HttpResponse,
  HttpResponseBadRequest,
  HttpResponseForbidden,
  HttpResponseNotAllowed,
  HttpResponseRedirect,
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


def home(request):
    base_url = request.build_absolute_uri()
    return render(request, "Artifactorial/home.html", {"base_url": base_url})


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


def _delete(request, filename):
    # Get the current user
    user = get_current_user(request,
                            request.GET.get('token', None))

    # The URL regexp removes the leading slash, so add it back
    filename = '/' + filename

    # Only valid for artifacts
    if filename[-1] == '/':
        return HttpResponseBadRequest()

    artifact = get_object_or_404(Artifact, path=filename.lstrip('/'))

    if not artifact.is_writable_to(user):
        return HttpResponseForbidden()

    artifact.delete()
    return HttpResponse('')


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
        directories = Directory.objects.filter(Q(path__startswith="%s" % (dirname)) | Q(path=dirname))
        directories = directories.select_related("user", "group")
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
        artifacts = artifacts.select_related("directory", "directory__user",
                                             "directory__group")
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
        if not dir_set and not art_list and not in_real_directory and not dirname_length == 0:
            raise Http404

        # Return the right formating (only html, json or yaml)
        formating = request.GET.get('format', 'html')
        content_types = {'html': 'text/html',
                         'json': 'application/json',
                         'yaml': 'application/yaml'}
        if formating not in ['html', 'json', 'yaml']:
            return HttpResponseBadRequest()

        # Build the breadcrumb
        breadcrumb = []
        url_accumulator = ''
        if dirname_length:
            for d in dirname[1:].split('/'):
                url_accumulator += d + '/'
                breadcrumb.append((d, url_accumulator))
        else:
            breadcrumb = []

        return render(request, "Artifactorial/list.%s" % formating,
                      {'directory': dirname,
                       'breadcrumb': breadcrumb,
                       'directories': sorted(dir_set),
                       'files': sorted(art_list),
                       'token': request.GET.get('token', None)},
                      content_type=content_types[formating])

    else:
        # Serving the file
        # TODO: use django-sendfile for better performances
        artifact = get_object_or_404(Artifact, path=filename.lstrip('/'))
        if not artifact.is_visible_to(user):
            return HttpResponseForbidden()

        # Guess the mimetype
        mime = mimetypes.guess_type(artifact.path.name)
        response = FileResponse(open(artifact.path.path, 'rb'),
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
        # TODO: does not work with alternate storage
        return HttpResponse(request.build_absolute_uri(reverse("artifacts",
                                                               args=[artifact.path.url])),
                            content_type='text/plain')
    else:
        return HttpResponseBadRequest()


@csrf_exempt
def artifacts(request, filename=''):
    if request.method == 'GET':
        return _get(request, filename)
    elif request.method == 'HEAD':
        return _head(request, filename)
    elif request.method == 'POST':
        return _post(request, filename)
    elif request.method == 'DELETE':
        return _delete(request, filename)
    else:
        return HttpResponseNotAllowed(['DELETE', 'GET', 'HEAD', 'POST'])


def directories(request):
    user = get_current_user(request,
                            request.GET.get('token', ''))
    dirs_query = Directory.objects.all().order_by("path") \
                          .select_related("user", "group") \
                          .prefetch_related("artifact_set")

    dirs = [(d, d.is_writable_to(user)) for d in dirs_query if d.is_visible_to(user)]
    return render(request, 'Artifactorial/directories/index.html',
                  {'directories': dirs})


@csrf_exempt
def shares_root(request):
    # Create a new sharing link
    if request.method == 'PUT':
        # Grab the requested file and check permissions
        put = QueryDict(request.body)
        filename = put.get('path', '')
        artifact = get_object_or_404(Artifact, path=filename.lstrip('/'))

        # Get the current user
        user = get_current_user(request,
                                put.get('token', ''))

        # Anonymous users are not allowed to create shares
        if user.is_anonymous():
            return HttpResponseForbidden()

        # The user should have the right to read the artifact
        if not artifact.is_visible_to(user):
            return HttpResponseForbidden()

        # Create the link
        share = Share(artifact=artifact, user=user)
        share.save()
        return HttpResponse(request.build_absolute_uri(reverse('shares', args=[share.token])),
                            content_type='text/plain')
    else:
        return HttpResponseNotAllowed(['PUT'])


def shares(request, token):
    if request.method == 'GET':
        share = get_object_or_404(Share, token=token)
        artifact = share.artifact

        # Guess the mimetype
        mime = mimetypes.guess_type(artifact.path.name)
        response = FileResponse(open(artifact.path.path, 'rb'),
                                content_type=mime[0] if mime[0]
                                else 'text/plain')

        response['Content-Length'] = artifact.path.size
        return response

    elif request.method == 'DELETE':
        # Get the current user
        user = get_current_user(request,
                                request.GET.get('token', ''))
        if user.is_anonymous():
            return HttpResponseForbidden()

        share = get_object_or_404(Share, token=token)
        # Only the owner can remove a share
        if share.user != user:
            return HttpResponseForbidden()

        share.delete()
        return HttpResponse('')

    else:
        return HttpResponseNotAllowed(['DELETE', 'PUT'])


@login_required
def tokens(request):
    if request.method == 'POST':
        description = request.POST.get('description', '')
        token = AuthToken.objects.create(user=request.user, description=description)
        token.save()

    tokens = AuthToken.objects.filter(user=request.user)
    return render(request, 'Artifactorial/tokens/index.html', {'tokens': tokens})


@login_required
def tokens_delete(request, id):
    get_object_or_404(AuthToken, user=request.user, id=id).delete()
    return HttpResponseRedirect(reverse('tokens.index'))


@login_required
def profile(request):
    return render(request, 'Artifactorial/accounts/profile.html')
