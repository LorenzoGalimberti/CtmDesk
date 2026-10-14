from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendario_view, name='calendario'),
    path('eventi/', views.eventi_json, name='eventi_json'),
    path('aggiungi_evento/', views.aggiungi_evento, name='aggiungi_evento'),
    path('evento/<int:event_id>/', views.evento_dettaglio, name='evento_dettaglio'),
    path('evento/elimina/<int:event_id>/', views.elimina_evento, name='elimina_evento'),
    path('evento/archivia/<int:event_id>/', views.archivia_evento, name='archivia_evento'),
    # path('evento/<int:event_id>/aggiungi-a-todo/', views.aggiungi_evento_a_todo, name='aggiungi_evento_a_todo'),
    path('lista_eventi/', views.ListaEventiView.as_view(), name='lista_eventi'),
]