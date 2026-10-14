from django.urls import path
from . import views

app_name = 'todo'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('add/', views.add_task, name='add_task'),
    path('complete/<int:task_id>/', views.complete_task, name='complete_task'),
    path('delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('<int:task_id>/archive/', views.archive_task, name='archive_task'),  # Aggiungi questa linea
    path('all-tasks/', views.all_task, name='all_task'),
    path('edit/<int:task_id>/', views.edit_task, name='edit_task'),  # Aggiungi questa linea per la modifica
    path('api/clienti/', views.get_clienti, name='get_clienti'),  # API per ottenere i clienti


]
