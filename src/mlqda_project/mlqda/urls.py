"""
mlqda_app url patterns

maps views to urls within the app
"""

from django.urls import path
from mlqda import views

app_name = 'mlqda'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('analyser-start/', views.analyser_start, name='analyser-start'),
    path('analyser-results/', views.analyser_results, name='analyser-results'),
    path('analyser-redirect/<collector_id>/', views.analyser_redirect, name='analyser-redirect'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq_page, name='faq'),
    path('download-zip-results/<file_name>/',
         views.download_zip_results,
         name='download-zip-results'),
]
