# activities/urls.py
from django.urls import path
from .views import (
    AttivitaListView, AttivitaDetailView, AttivitaCreateView, AttivitaUpdateView, AttivitaDeleteView,
    RichiedenteListView, RichiedenteDetailView, RichiedenteCreateView, RichiedenteUpdateView, RichiedenteDeleteView,
    CategoriaListView, CategoriaDetailView, CategoriaCreateView, CategoriaUpdateView, CategoriaDeleteView,
    chiudi_attivita, riapri_attivita, dashboard_activities,
    carica_allegato, scarica_allegato, anteprima_allegato, elimina_allegato
)

urlpatterns = [
    # Dashboard
    path('', dashboard_activities, name='activities-dashboard'),
    
    # CRUD per Attività
    path('attivita/', AttivitaListView.as_view(), name='attivita-list'),
    path('attivita/<int:pk>/', AttivitaDetailView.as_view(), name='attivita-detail'),
    path('attivita/create/', AttivitaCreateView.as_view(), name='attivita-create'),
    path('attivita/<int:pk>/update/', AttivitaUpdateView.as_view(), name='attivita-update'),
    path('attivita/<int:pk>/delete/', AttivitaDeleteView.as_view(), name='attivita-delete'),
    
    # Azioni per Attività
    path('attivita/<int:pk>/chiudi/', chiudi_attivita, name='attivita-chiudi'),
    path('attivita/<int:pk>/riapri/', riapri_attivita, name='attivita-riapri'),
    
    # Allegati
    path('attivita/<int:attivita_id>/allegato/', carica_allegato, name='carica-allegato'),
    path('allegato/<int:allegato_id>/scarica/', scarica_allegato, name='scarica-allegato'),
    path('allegato/<int:allegato_id>/anteprima/', anteprima_allegato, name='anteprima-allegato'),
    path('allegato/<int:allegato_id>/elimina/', elimina_allegato, name='elimina-allegato'),
    
    # CRUD per Categorie
    path('categorie/', CategoriaListView.as_view(), name='categoria-list'),
    path('categorie/<int:pk>/', CategoriaDetailView.as_view(), name='categoria-detail'),
    path('categorie/create/', CategoriaCreateView.as_view(), name='categoria-create'),
    path('categorie/<int:pk>/update/', CategoriaUpdateView.as_view(), name='categoria-update'),
    path('categorie/<int:pk>/delete/', CategoriaDeleteView.as_view(), name='categoria-delete'),
    
    # CRUD per Richiedenti
    path('richiedenti/', RichiedenteListView.as_view(), name='richiedente-list'),
    path('richiedenti/<int:pk>/', RichiedenteDetailView.as_view(), name='richiedente-detail'),
    path('richiedenti/create/', RichiedenteCreateView.as_view(), name='richiedente-create'),
    path('richiedenti/<int:pk>/update/', RichiedenteUpdateView.as_view(), name='richiedente-update'),
    path('richiedenti/<int:pk>/delete/', RichiedenteDeleteView.as_view(), name='richiedente-delete'),
]