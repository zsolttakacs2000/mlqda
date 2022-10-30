"""
File to keep track of models
"""

from django.db import models
from django.conf import settings


class FileCollector(models.Model):
    first_name = models.TextField()


class FileContainer(models.Model):
    first_name = models.ForeignKey(FileCollector, on_delete=models.CASCADE)
    file = models.FileField(upload_to=settings.MEDIA_ROOT)
