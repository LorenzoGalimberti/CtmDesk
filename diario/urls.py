from django.urls import path
from .views import *

app_name = 'diario'  # Questo è il namespace

urlpatterns = [
    path('', diario_list, name='diario_list'),
    path('<int:anno>/<int:mese>/<int:giorno>/nuovo/', nuovo_diario, name='nuovo_diario'),
    path('<int:anno>/<int:mese>/<int:giorno>/', diario_del_giorno, name='diario_del_giorno'),
    path('<int:pk>/', dettaglio_diario, name='dettaglio_diario'),
    path('<int:pk>/modifica/', aggiorna_diario, name='aggiorna_diario'),
    path('<int:pk>/cancella/', cancella_diario, name='cancella_diario'),
    # Nuova URL per il download
    path('<int:pk>/scarica/', scarica_nota_pdf, name='scarica_nota_pdf'),
]