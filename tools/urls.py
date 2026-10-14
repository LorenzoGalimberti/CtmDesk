from django.urls import path
from . import views

app_name = 'tools'  # Per il namespace

urlpatterns = [
    path('', views.index, name='index'),
    path('impatti-fermi/', views.impatti_fermi, name='impatti_fermi'),
]