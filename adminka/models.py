from django.db import models
from django.utils.html import mark_safe
import os
from django.conf import settings
from django.utils.deconstruct import deconstructible

import uuid

# Create your models here.


@deconstructible
class UploadToPathAndRename(object):

    def __init__(self, path):
        self.sub_path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # get filename
        if instance.pk:
            filename = '{}.{}'.format(instance.pk, ext)
        else:
            # set filename as random string
            filename = '{}.{}'.format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.sub_path, filename)

class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    photo = models.ImageField(upload_to=UploadToPathAndRename(settings.PHOTOS_URL), blank=True)
    location = models.CharField('location', max_length=255, blank=False)
    user = models.CharField('user', max_length=255, blank=False)
    # auto_now_add автоматически выставит дату создания записи
    created_at = models.DateTimeField(auto_now_add=True)
    # auto_now изменятся при каждом обновлении записи
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Изображение от пользователя {self.user} с локации {self.location}'

    def image_preview(self):
        return mark_safe('<img src="/%s" width="64"/>' % (self.photo))

    def image_tag(self):
        return mark_safe('<img src="/%s" width="150"/>' % (self.photo))

    image_tag.short_description = 'Image'

    class Meta:
        db_table = "photo"
        verbose_name = 'Фото'
        verbose_name_plural = 'Фотографии'
