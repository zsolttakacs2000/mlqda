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
    path('topic-modelling-start/', views.topic_modelling_start, name='topic-modelling-start'),
    path('topic-modelling-results/<collector_id>/',
         views.topic_modelling_results,
         name='topic-modelling-results'),
    path('sentiment-start/', views.sentiment_start, name='sentiment-start'),
    path('sentiment-results/<collector_id>/', views.sentiment_results, name='sentiment-results'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq_page, name='faq'),
    path('download-files/<file_name>/',
         views.download_files,
         name='download-files'),

]
