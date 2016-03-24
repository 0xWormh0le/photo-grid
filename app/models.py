from __future__ import unicode_literals

import os

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.contrib.auth.models import User

from PIL import Image, ImageFilter


# Associate filter strings from viewsets to ImageFilter effects
FILTERS = {
	'BLUR': ImageFilter.BLUR,
	'EMBOSS': ImageFilter.EMBOSS,
	'DETAIL': ImageFilter.DETAIL,
	'CONTOUR': ImageFilter.CONTOUR,
	'SMOOTH': ImageFilter.SMOOTH,
	'SHARPEN': ImageFilter.SHARPEN
}


class Photo(models.Model):
	"""Photo ORM model.
	"""
	photo_id = models.AutoField(primary_key=True)
	path = models.ImageField(upload_to='photo/')
	owner = models.ForeignKey(User, on_delete=models.CASCADE)

	def use_effect(self, effect, photo_edit):
		"""Modifies an image with the specified effect.
		"""
		if effect in FILTERS:
			photo = Image.open(photo_edit.upload)
			photo = photo.filter(FILTERS.get(effect))

			photo.save(photo_edit.upload.url[1:])

	def get_file_name(self):
		"""Returns the name of the file that this model is associated with.
		"""
		return self.path.name[2:]

	def __str__(self):
		"""Customize representation of this model's instance.
		"""
		return '{0}'.format(self.path.name[2:])


# def photo_edit_directory_path(instance, filename):
# 	"""Specify folder where Photo edits will be persisted."""
# 	return '/photo_edits/'


class PhotoEdit(models.Model):
	"""Associate edits with a Photo.
	"""
	photo_edit_id = models.AutoField(primary_key=True)
	photo = models.ForeignKey(Photo)
	upload = models.ImageField(upload_to='edits/')


def effects_file_name(instance, filename):
	"""Return upload path to be used in path attribute of Effects model.
	"""
	filetime = instance.file_name + instance.effect_name
	return 'effects/{0}'.format(filetime + '.jpg')


# Create your models here.
class Effects(models.Model):
	"""Photo edit effects preview ORM.
	"""
	effect_id = models.AutoField(primary_key=True)
	effect_name = models.CharField(max_length=20)
	file_name = models.CharField(max_length=50)
	path = models.ImageField(upload_to=effects_file_name)

	def use_effect(self):
		"""Apply the effect that corresponds to current value of 'self.effect_name'
		in the FILTERS dictionary.
		"""
		if self.effect_name in FILTERS:
			photo = Image.open(self.path)
			preview = photo.filter(FILTERS.get(self.effect_name))
			preview.save(self.path.url[1:])

	def save(self, *args, **kwargs):
		"""Apply the effects to the file on disk whenever model.save() is called.

		This method is called after save because the 'path' attribute will refer
		to 'MEDIA_ROOT' until the model instance is saved. After saving, it refers
		to 'MEDIA_ROOT/effects/' (which is where we want effects to be uploaded
		when applying effect previews).
		"""
		super(Effects, self).save(*args, **kwargs)

		self.use_effect()

	def __str__(self):
		"""Customize representation of this model's instance.
		"""
		return '{0}{1}'.format(self.file_name, self.effect_name)


class SocialAuthUsersocialauth(models.Model):
	"""
	A read only ORM to query information that is populated by python-social-auth
	in the 'social_auth_usersocialauth' table.
	"""
	id = models.IntegerField(primary_key=True)
	provider = models.CharField(max_length=32)
	uid = models.CharField(max_length=255)
	extra_data = models.TextField()
	user = models.ForeignKey(User, models.DO_NOTHING)

	class Meta:
		managed = False
		db_table = 'social_auth_usersocialauth'
		unique_together = (('provider', 'uid'),)

	def __str__(self):
		"""Customize representation of this model's instance.
		"""
		return '{0}{1}'.format(self.user.username, self.provider)


@receiver(post_delete, sender=Effects)
def file_cleanup(sender, **kwargs):
	"""This method deletes associated photo files on disk every time 'delete()'
	is called on a model instance (or on a queryset of Effect objects).
	"""
	instance = kwargs.get('instance')
	filename = instance.path.url[1:]
	if os.path.exists(filename):
			os.remove(filename)
