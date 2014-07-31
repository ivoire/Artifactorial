from django.contrib import admin

from Artifactorial.models import AuthToken, Artifact, Directory


class ArtifactAdmin(admin.ModelAdmin):
    list_display = ('path', 'directory', 'is_permanent')


class DirectoryAdmin(admin.ModelAdmin):
    list_display = ('path', 'user', 'group', 'is_public')

admin.site.register(AuthToken)
admin.site.register(Artifact, ArtifactAdmin)
admin.site.register(Directory, DirectoryAdmin)
