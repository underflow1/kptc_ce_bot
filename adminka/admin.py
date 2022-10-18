from django.contrib import admin
from .models import Photo

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'user', 'location', 'created_at')
    fields = ('photo', 'image_tag', 'location', 'user')
    readonly_fields = ('image_tag',)
    pass
