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
from mlqda.sentiment_analyser import SentimentAnalyser

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


def topic_modelling_start(request):
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
            return redirect(reverse('mlqda:topic-modelling-results',
                                    kwargs={'collector_id': collector.collector_id}))
    else:
        form = FileForm()
    context_dict['form'] = form
    return render(request, 'mlqda/topic_modelling_start.html', context=context_dict)


def contact(request):
    """
    Function to link contact view
    @param request: incoming request
    @return: rendered about page as an html - mlqda/contact.html
    """
    context_dict = {}
    return render(request, 'mlqda/contact.html', context=context_dict)


def topic_modelling_results(request, collector_id):
    """
    Function to link result view of the analyser
    @param request: incoming request
    @return: rendered about page as an html with the results included in the
    context dictionary - mlqda/analyser_results.html
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
    context_dict['result_path'] = tm.zip_name
    context_dict['collector_id'] = collector_id
    return render(request, 'mlqda/topic_modelling_results.html', context=context_dict)


def faq_page(request):
    """
    Function to link the FAQ view to the  correct template
    @param request: incoming request
    @return: rendered about page as an html - mlqda/faq.html
    """
    context_dict = {}
    return render(request, 'mlqda/faq.html', context=context_dict)


def download_files(request, file_name):
    """
    Function to enable file downoad of results. Takes file name as a parameter.
    Finds FileContainer object based on file name and downloads the appropriate file.
    """
    result_file = FileContainer.objects.filter(file_name=file_name)[0]
    response = FileResponse(open(str(result_file.file), 'rb'))
    return response


def sentiment_start(request):
    """
    Function to link to the starting view of the sentiment analyser
    @param request: incoming request
    @return: rendered start page (mlqda/analyser_start.html)
    or the redirect page (mlqda/analyser-redirect)
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
            return redirect(reverse('mlqda:sentiment-results',
                                    kwargs={'collector_id': collector.collector_id}))
    else:
        form = FileForm()
    context_dict['form'] = form
    return render(request, 'mlqda/sentiment_start.html', context=context_dict)


def sentiment_results(request, collector_id):
    """
    Function to display sentiment analysis reuslts
    @param request: incoming request
    @param collector_id: collector_id to identify a set of documents requres for the analysis
    @return: rendered sentiment results page as an html - mlqda/sentiment_results.html
    """
    context_dict = {}
    collector = FileCollector.objects.get(collector_id=collector_id)
    files = FileContainer.objects.filter(first_name=collector)

    datafiles_paths = []
    for file in files:
        path = os.path.join(settings.MEDIA_DIR, str(file.file))
        datafiles_paths.append(path)

    sa = SentimentAnalyser(datafiles_paths, collector_id)
    sa.create_pdf_results()
    sa.create_csv_results()
    result = sa.compile_results()

    context_dict['result_path'] = result
    context_dict['collector_id'] = collector_id
    return render(request, 'mlqda/sentiment_results.html', context=context_dict)


def delete_container(request, delete_id):
    """
    Function to handle file deletion. Based on collector id, the function finds the collector
    and deletes all related files.txt
    @param request: incoming request
    @param collector_id: collector_id to identify a set of documents requres for the analysis
    @return: redrirects to index. Rendered index page - mlqda/index.html
    """
    collector_id = delete_id
    collector = FileCollector.objects.get(collector_id=collector_id)
    files = FileContainer.objects.filter(first_name=collector)

    for file in files:
        file.delete()
        if os.path.exists(str(file.file)):
            print(str(file.file))
            os.remove(str(file.file))

    collector.delete()

    return redirect(reverse('mlqda:index'))


def error_view(request):
    return render(request, 'mlqda/error.html', context={})


def guides(request):
    return render(request, "mlqda/guides.html", context={})
