from django.db import models
from django.utils.html import mark_safe
import os
from django.conf import settings
from django.utils.deconstruct import deconstructible
import uuid

# Create your models here.

nb = dict(null=True, blank=True)


class CreateTracker(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class CreateUpdateTracker(CreateTracker):
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(CreateTracker.Meta):
        abstract = True


class Location(CreateUpdateTracker):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256, unique=True)

    @classmethod
    def get_location_by_id(cls, location_id: uuid):
        """ Search user in DB, return User or None if not found """
        return cls.objects.filter(id=location_id).first()

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
        if self.last_name:
            white_space = " "
        else:
            white_space = ""
        return f'{self.first_name or ""}{white_space}{self.last_name or ""}'

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
            filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.sub_path, filename)


class Photo(CreateUpdateTracker):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    photo = models.ImageField(upload_to=UploadToPathAndRename(settings.PHOTOS_URL), blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        db_table = "photo"
        verbose_name = 'Фото'
        verbose_name_plural = 'Фотографии'

    def __str__(self):
        return f'Изображение от пользователя {self.user} с локации {self.location}'

    def image_preview(self):
        return mark_safe('<img src="/%s" width="64"/>' % (self.photo))

    def image_tag(self):
        return mark_safe('<img src="/%s" width="150"/>' % (self.photo))

    image_tag.short_description = 'Image'
