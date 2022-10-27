"""
Python files to contain views for the MLQDA webapp
"""

from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings

from mlqda.forms import FileForm
import os
from pathlib import Path


def save_file(file):
    """
    Helper function to save files to media folder
    @param file: file to be saved
    @return: None
    """
    my_media_root = settings.MEDIA_ROOT
    file_name = str(file)
    file_path = os.path.join(my_media_root, file_name)
    output_file = Path(file_path)
    output_file.parent.mkdir(exist_ok=True, parents=True)
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def index(request):
    """
    Function to link index/home view
    @param request: incoming request
    @return: rendered home page as an html - mlqda/index.html
    """
    context_dict = {}
    return render(request, 'mlqda/index.html', context=context_dict)


def about(request):
    """
    Function to link about view
    @param request: incoming request
    @return: rendered about page as an html - mlqda/about.html
    """
    context_dict = {}
    return render(request, 'mlqda/about.html', context=context_dict)


def analyser_start(request):
    """
    Function to link to the starting view of the analyser
    @param request: incoming request
    @return: rendered start page (mlqda/index.html) or the redirect page (mlqda/analyser-redirect)
    """
    context_dict = {}
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')
            for file in files:
                save_file(file)
            return redirect(reverse('mlqda:analyser-redirect'))
    else:
        form = FileForm()
    context_dict['form'] = form
    return render(request, 'mlqda/analyser_start.html', context=context_dict)


def contact(request):
    """
    Function to link contact view
    @param request: incoming request
    @return: rendered about page as an html - mlqda/contact.html
    """
    context_dict = {}
    return render(request, 'mlqda/contact.html', context=context_dict)


def analyser_results(request):
    """
    Function to link result view of the analyser
    @param request: incoming request
    @return: rendered about page as an html with the results included in the
    context dictionary - mlqda/analyser_results.html
    """
    context_dict = {'topics': {'Topic 1': [('Network', 0.0300),
                                           ('Connection', 0.0280),
                                           ('Internet', 0.0250),
                                           ('System', 0.0240),
                                           ('Socket', 0.0150)],
                               'Topic 2': [('Education', 0.0250),
                                           ('Classroom', 0.0240),
                                           ('Lecture', 0.0190),
                                           ('School', 0.0180),
                                           ('University', 0.0170)]
                               }
                    }
    context_dict['total_topics'] = len(context_dict['topics'])
    return render(request, 'mlqda/analyser_results.html', context=context_dict)


def analyser_redirect(request):
    """
    Function to link the redirect view of the analyser
    @param request: incoming request
    @return: rendered about page as an html - mlqda/analyser_redirect.html
    """
    context_dict = {}
    return render(request, 'mlqda/analyser_redirect.html', context=context_dict)


def faq_page(request):
    """
    Function to link the FAQ view to the  correct template
    @param request: incoming request
    @return: rendered about page as an html - mlqda/faq.html
    """
    context_dict = {}
    return render(request, 'mlqda/faq.html', context=context_dict)
