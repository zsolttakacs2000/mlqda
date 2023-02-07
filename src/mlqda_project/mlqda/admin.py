"""
Python file to alter the Django admin interface
"""
from django.contrib import admin
from mlqda.models import FileContainer, FileCollector

admin.site.register(FileContainer)
admin.site.register(FileCollector)
