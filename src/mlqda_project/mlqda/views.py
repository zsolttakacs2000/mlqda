from django.shortcuts import render, redirect
from django.http import HttpResponse
from mlqda.forms import FileForm
from django.urls import reverse


def save_file(file):
    file_name = str(file)
    file_path = 'media/' + file_name
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

def index(request):
    context_dict = {}
    return render(request, 'mlqda/index.html', context=context_dict)

def about(request):
    context_dict = {}
    return render(request, 'mlqda/about.html', context=context_dict)

def analyser_start(request):
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
    context_dict = {}
    return render(request, 'mlqda/contact.html', context=context_dict)

def analyser_results(request):
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
    context_dict = {}
    return render(request, 'mlqda/analyser_redirect.html', context=context_dict)