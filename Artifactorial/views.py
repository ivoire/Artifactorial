# -*- coding: utf-8 -*-
# vim: set ts=4

from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from Artifactorial.models import Artifact, Directory

import os


def index(request):
    artifacts = Artifact.objects.all()

    return render_to_response('Artifactorial/index.html',
                              {'artifacts': artifacts},
                              context_instance=RequestContext(request))


class ArtifactForm(ModelForm):
    class Meta:
        model = Artifact
        fields = ('path', 'directory', 'is_permanent')


@csrf_exempt
def post(request):
    if request.method == 'POST':
        # Find the directory by name
        directory_path = request.POST.get('directory', '')
        directory_id = get_object_or_404(Directory, path=directory_path)
        request.POST['directory'] = directory_id.id

        # TODO: validate the user, group or public rights
        # Validate the updated form
        form = ArtifactForm(request.POST, request.FILES)
        if form.is_valid():
            artifact = form.save()
            return HttpResponse(artifact.path.url, content_type='text/plain')
        else:
            raise PermissionDenied
    else:
        raise PermissionDenied


def get(request, filename):
    data=''
    # Is it a file or a path
    if filename[-1] == '/':
        dirname = os.path.dirname(filename)
        directories = Directory.objects.filter(Q(path__startswith="%s" % (dirname)) | Q(path=dirname))
        if not directories:
            # TODO: Look for pseudo directories with files
            raise Http404

        dirname_length = len(dirname)
        # Special case for the root directory
        if dirname == '/':
            dirname_length = 0

        dir_set = set()
        for directory in directories:
            if directory.path != dirname:
                # Sub directory => print the next elements in the path
                full_dir_name = directory.path[dirname_length+1:]
                try:
                    index = full_dir_name.index('/')
                    dir_set.add(full_dir_name[:index])
                except Exception:
                    dir_set.add(full_dir_name)

        artifacts = Artifact.objects.filter(path__startswith=filename.lstrip('/'))
        art_set = set()
        for artifact in artifacts:
            # TODO: handle pseudo directories
            art_set.add(artifact.path.name[dirname_length:])

        return render_to_response('Artifactorial/list.html',
                                  {'directory': dirname, 'directories': dir_set,
                                   'files': art_set},
                                  context_instance=RequestContext(request))
    else:
        artifact = get_object_or_404(Artifact, path=filename.lstrip('/'))
        data = "%s (%d)" % (artifact.path.name, artifact.path.size)
        return HttpResponse(data)
