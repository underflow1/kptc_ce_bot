from django.db import models
from django.utils.html import mark_safe
import os
from django.conf import settings
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet, Manager

import uuid

# Create your models here.

nb = dict(null=True, blank=True)


class CreateTracker(models.Model):
    # auto_now_add автоматически выставит дату создания записи
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class CreateUpdateTracker(CreateTracker):
    # auto_now изменятся при каждом обновлении записи
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(CreateTracker.Meta):
        abstract = True


class Location(CreateUpdateTracker):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256, **nb)

    class Meta:
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'

    def __str__(self):
        return f'{self.name}'


class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(primary_key=True, help_text="Telegram client's id")  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(max_length=8, help_text="Telegram client's lang", **nb)
    comment = models.CharField(max_length=256, **nb)
    allowed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


    def __str__(self):
        return f'{self.user_id} {self.username} {self.last_name} {self.first_name}'

    @classmethod
    def get_user_by_user_id(cls, user_id: int):
        """ Search user in DB, return User or None if not found """
        return cls.objects.filter(user_id=user_id).first()


    @classmethod
    def get_user_allowed_user_id(cls, user_id: int):
        """ Search user in DB, return User or None if not found """
        field_name = 'allowed'
        user = cls.objects.filter(user_id=user_id).first()
        field_value = getattr(user, field_name)
        return field_value



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


class Photo(CreateUpdateTracker):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    photo = models.ImageField(upload_to=UploadToPathAndRename(settings.PHOTOS_URL), blank=True)
    location = models.CharField('location', max_length=255, blank=False)
    user = models.CharField('user', max_length=255, blank=False)

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'

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
