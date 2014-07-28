# -*- coding: utf-8 -*-
# vim: set ts=4

from django.forms import ModelForm
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from Artifactor.models import Artifact


def index(request):
    artifacts = Artifact.objects.all()

    return render_to_response('Artifactor/index.html',
                              {'artifacts': artifacts},
                              context_instance=RequestContext(request))


class ArtifactForm(ModelForm):
    class Meta:
        model = Artifact
        fields = ('path',)


@csrf_exempt
def post(request):
    if request.method == 'POST':
        form = ArtifactForm(request.POST, request.FILES)
        if form.is_valid():
            artifact = form.save()
            return HttpResponse(artifact.path.url, content_type='text/plain')
    else:
        raise Http404
