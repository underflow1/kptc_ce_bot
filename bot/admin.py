from django.contrib import admin
from .models import Photo, User, Location

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)
    list_display = ('image_preview', 'user', 'location', 'created_at')
    fields = ('photo', 'image_tag', 'location', 'user')
    readonly_fields = ('photo', 'image_tag', 'location', 'user')
    pass

@admin.register(User)
class PhotoAdmin(admin.ModelAdmin):
    ordering = ('-created_at',)
    readonly_fields = ('user_id', 'username', 'first_name', 'last_name', 'language_code')
    list_display = ('user_id', 'username', 'first_name', 'last_name', 'allowed', 'comment', 'created_at')
    fields = ('user_id', 'username', 'first_name', 'last_name', 'allowed', 'comment')
    pass


@admin.register(Location)
class PhotoAdmin(admin.ModelAdmin):
    ordering = ('name',)
