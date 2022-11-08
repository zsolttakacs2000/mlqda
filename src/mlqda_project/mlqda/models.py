"""
File to keep track of models
"""

from django.db import models
from django.conf import settings

import os


class FileCollector(models.Model):
    collector_id = models.AutoField(primary_key=True)
    first_name = models.TextField(max_length=512)


class FileContainer(models.Model):
    file_id = models.AutoField(primary_key=True)
    first_name = models.ForeignKey(FileCollector, on_delete=models.CASCADE)
    file = models.FileField(upload_to=os.path.relpath(settings.MEDIA_ROOT, start = os.curdir),
                            max_length=256)
    file_name = models.CharField(max_length=512, null=True)

    def save(self, *args, **kwargs):
        self.file_name = str(os.path.basename(str(self.file)))
        super(FileContainer, self).save(*args, **kwargs)
