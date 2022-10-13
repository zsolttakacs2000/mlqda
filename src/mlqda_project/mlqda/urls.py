from django.urls import path
from mlqda import views

app_name = 'mlqda'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
]
