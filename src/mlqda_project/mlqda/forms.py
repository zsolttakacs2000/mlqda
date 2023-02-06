"""
Python file to collect required forms for MLQDA webapp
"""
from django import forms

from mlqda.models import FileContainer


class FileForm(forms.Form):
    """
    Form class to enable the upload of multiple files
    """
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={
        'multiple': True,
        'accept': '.pdf,.docx,.txt,.csv,.xlsx'
        }))

    class Meta:
        model = FileContainer
        fields = ['file']
