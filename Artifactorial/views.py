# -*- coding: utf-8 -*-
# vim: set ts=4

from django.core.exceptions import PermissionDenied
from django.forms import ModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from Artifactorial.models import Artifact, Directory


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
