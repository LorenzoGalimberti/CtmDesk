from django.contrib import admin
from .models import Diario,Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('nome', 'colore_sfondo', 'colore_testo')
@admin.register(Diario)
class DiarioAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'contenuto', 'data_creazione')  # Mostra titolo, contenuto e data creazione
    list_filter = ('data_creazione',)  # Filtro per data di creazione
    search_fields = ('titolo', 'contenuto')  # Aggiungi funzionalità di ricerca per titolo e contenuto
    ordering = ('-data_creazione',)  # Ordina per data creazione decrescente
