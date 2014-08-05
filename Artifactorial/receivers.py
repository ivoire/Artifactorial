from __future__ import unicode_literals

from django.db.models.signals import post_delete
from django.dispatch import receiver
from Artifactorial.models import Artifact


@receiver(post_delete, sender=Artifact)
def artifact_post_delete(sender, **kwargs):
    artifact = kwargs['instance']
    artifact.path.storage.delete(artifact.path.path)
