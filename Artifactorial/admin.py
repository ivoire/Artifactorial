from django.contrib import admin
from django.template.defaultfilters import filesizeformat

from Artifactorial.models import AuthToken, Artifact, Directory


class ArtifactAdmin(admin.ModelAdmin):
    list_display = ('path', 'directory', 'is_permanent', 'created_at')


class DirectoryAdmin(admin.ModelAdmin):
    def current_size(self, obj):
        return "%s / %s" % (filesizeformat(obj.size()),
                            filesizeformat(obj.quota))

    list_display = ('path', 'user', 'group', 'is_public', 'ttl', 'current_size')


admin.site.register(AuthToken)
admin.site.register(Artifact, ArtifactAdmin)
admin.site.register(Directory, DirectoryAdmin)
