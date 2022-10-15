from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    context_dict = {}
    return render(request, 'mlqda/index.html', context=context_dict)

def about(request):
    return HttpResponse('about')

def analyser(request):
    return HttpResponse('analyser')

def contact(request):
    context_dict = {}
    return render(request, 'mlqda/contact.html', context=context_dict)