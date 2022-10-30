"""
Python files to contain views for the MLQDA webapp
"""

from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings

from mlqda.forms import FileForm
from mlqda.models import FileCollector, FileContainer
from mlqda.topic_modelling import TopicModelling

import os
from pprint import pprint
import re


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

    full_text = []
    for file in files:
        path = os.path.join(settings.MEDIA_ROOT, str(file.file))

        with open(path, 'r') as f:
            text = f.read().replace('\n', '')
            full_text.append(text)

    tm = TopicModelling(full_text)
    tm.process_files()
    tm.create_helper_datastructures()
    tm.run_lda()
    my_model = tm.get_lda_output()
    pprint(my_model)
    result_dict = {}
    for topic in my_model:
        topic_contrib = []
        contrib_string = str(topic[1])
        contrib_string = re.sub("'", "", contrib_string)
        contrib_string = re.sub('"', '', contrib_string)
        contrib_string = re.sub(" ", "", contrib_string)
        values = contrib_string.split("+")
        for contribution in values:
            contrib_list = contribution.split('*')
            contrib_tuple = (float(contrib_list[0]), str(contrib_list[1]).strip())
            topic_contrib.append(contrib_tuple)

        result_dict[str(int(topic[0])+1)] = topic_contrib
    print(result_dict)
    context_dict['topics'] = result_dict
    context_dict['total_topics'] = len(context_dict['topics'])
    return render(request, 'mlqda/analyser_results.html', context=context_dict)


def faq_page(request):
    """
    Function to link the FAQ view to the  correct template
    @param request: incoming request
    @return: rendered about page as an html - mlqda/faq.html
    """
    context_dict = {}
    return render(request, 'mlqda/faq.html', context=context_dict)
