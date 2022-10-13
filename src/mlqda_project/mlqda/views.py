from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse('index')

def about(request):
    return HttpResponse('about')