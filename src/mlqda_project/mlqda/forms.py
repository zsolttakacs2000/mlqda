"""
Python file to collect required forms for MLQDA webapp
"""
from django import forms


class FileForm(forms.Form):
    """
    Form class to enable the upload of multiple files
    """
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
