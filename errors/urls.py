from django.urls import path
from . import views

urlpatterns = [
    path('', views.errore_list, name='errore_list'),
    path('new/', views.errore_create, name='errore_create'),
    path('<int:pk>/edit/', views.errore_update, name='errore_update'),
    path('<int:pk>/delete/', views.errore_delete, name='errore_delete'),
    path('<int:pk>/', views.errore_detail, name='errore_detail'),  # URL per dettaglio
]
