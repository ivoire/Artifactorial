from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

import datetime
import os


@python_2_unicode_compatible
class Directory(models.Model):
    path = models.CharField(max_length=300, null=False, blank=False)
    user = models.ForeignKey(User, null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Directories'

    def clean(self):
        """
        Artifacts should be owned by one group or one user, not both.
        """
        if self.user is not None and self.group is not None:
            raise ValidationError("Cannot be owned by user and group")
        if self.user is None and self.group is None and not self.is_public:
            raise ValidationError("An anonymous directory should be public")
        if not os.path.normpath(self.path) == self.path:
            raise ValidationError({'path': ['Expecting a normalized path and '\
                                            'without leading slash']})
        if not os.path.isabs(self.path):
            raise ValidationError({'path': ['Expecting an absolute path']})

    def __str__(self):
        if self.user is not None:
            return "%s (%s)" % (self.path, self.user.get_fullname())
        elif self.group is not None:
            return "%s (%s)" % (self.path, self.group)
        else:
            return "%s (anonymous)" % (self.path)


def get_path_name(instance, filename):
    now = datetime.datetime.now()
    date_str = now.strftime('%Y/%m/%d/%M')
    return os.path.normpath('/'.join(['artifact', instance.directory.path,
                                      date_str, filename]))


@python_2_unicode_compatible
class Artifact(models.Model):
    path = models.FileField(upload_to=get_path_name)
    directory = models.ForeignKey(Directory, blank=False)

    def __str__(self):
        return self.path.name
