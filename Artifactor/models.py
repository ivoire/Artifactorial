from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Artifact(models.Model):
    path = models.FileField(upload_to='artifacts/%Y/%m/%d')

    def __str__(self):
        return self.path.name
