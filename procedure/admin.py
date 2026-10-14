from django.contrib import admin
from .models import Ambiente, Cliente, Tipologia, Procedura, Step

@admin.register(Ambiente)
class AmbienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)

@admin.register(Tipologia)
class TipologiaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)

@admin.register(Procedura)
class ProceduraAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'ambiente', 'cliente', 'tipologia')
    list_filter = ('ambiente', 'cliente', 'tipologia')
    search_fields = ('nome',)

@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ('id', 'titolo', 'procedura')
    list_filter = ('procedura',)
    search_fields = ('titolo', 'corpo')
