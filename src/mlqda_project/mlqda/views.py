"""
Python files to contain views for the MLQDA webapp
"""

from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.http import FileResponse

from mlqda.forms import FileForm
from mlqda.models import FileCollector, FileContainer
from mlqda.topic_modelling import TopicModelling

import os


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
            collector = FileCollector(first_name=str(files[0]))
            collector.save()
            for file in files:
                current_file = FileContainer.objects.create(file=file, first_name=collector)
                current_file.save()
            return redirect(reverse('mlqda:analyser-redirect',
                                    kwargs={'collector_id': collector.collector_id}))
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
    # context_dict = {'topics': {'Topic 1': [('Network', 0.0300),
    #                                        ('Connection', 0.0280),
    #                                        ('Internet', 0.0250),
    #                                        ('System', 0.0240),
    #                                        ('Socket', 0.0150)],
    #                            'Topic 2': [('Education', 0.0250),
    #                                        ('Classroom', 0.0240),
    #                                        ('Lecture', 0.0190),
    #                                        ('School', 0.0180),
    #                                        ('University', 0.0170)]
    #                            }
    #                 }
    # context_dict['total_topics'] = len(context_dict['topics'])
    # return render(request, 'mlqda/analyser_results.html', context=context_dict)


def analyser_redirect(request, collector_id):
    """
    Function to link the redirect view of the analyser
    @param request: incoming request
    @return: rendered about page as an html - mlqda/analyser_redirect.html
    """
    context_dict = {}
    collector = FileCollector.objects.get(collector_id=collector_id)
    files = FileContainer.objects.filter(first_name=collector)

    datafiles_paths = []
    for file in files:
        path = os.path.join(settings.MEDIA_DIR, str(file.file))
        datafiles_paths.append(path)

    tm = TopicModelling(datafiles_paths, collector_id)
    tm.process_files()
    tm.create_helper_datastructures()
    tm.tf_idf_removal()
    tm.dynamic_lda()
    tm.compile_results()
    context_dict['topics'] = tm.result_dict
    context_dict['total_topics'] = len(context_dict['topics'])
    context_dict['zip_name'] = tm.zip_name
    return render(request, 'mlqda/analyser_results.html', context=context_dict)


def faq_page(request):
    """
    Function to link the FAQ view to the  correct template
    @param request: incoming request
    @return: rendered about page as an html - mlqda/faq.html
    """
    context_dict = {}
    return render(request, 'mlqda/faq.html', context=context_dict)


def download_zip_results(request, file_name):
    """
    Function to enable zip file downoad of results. Takes file name as a parameter.
    Finds FileContainer object based on file name and downloads the appropriate file.
    """
    result_file = FileContainer.objects.filter(file_name=file_name)[0]
    response = FileResponse(open(str(result_file.file), 'rb'))
    return response
