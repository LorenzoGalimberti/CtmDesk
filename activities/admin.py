# activities/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Attivita, Richiedente, Categoria, AllegatoAttivita

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'colore_badge', 'icona_display', 'ordinamento', 'attiva', 'num_attivita', 'created_at']
    list_filter = ['attiva', 'created_at']
    search_fields = ['nome', 'descrizione']
    list_per_page = 25
    ordering = ['ordinamento', 'nome']
    
    fieldsets = (
        ('Informazioni Base', {
            'fields': ('nome', 'descrizione')
        }),
        ('Aspetto', {
            'fields': ('colore', 'icona', 'ordinamento')
        }),
        ('Stato', {
            'fields': ('attiva',)
        }),
    )
    
    def colore_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            obj.colore,
            obj.nome
        )
    colore_badge.short_description = 'Anteprima'
    
    def icona_display(self, obj):
        return format_html('<i class="{}"></i>', obj.icona)
    icona_display.short_description = 'Icona'
    
    def num_attivita(self, obj):
        count = obj.attivita_count
        if count > 0:
            url = reverse('admin:activities_attivita_changelist') + f'?categoria__id__exact={obj.id}'
            return format_html('<a href="{}">{} attività</a>', url, count)
        return '0 attività'
    num_attivita.short_description = 'Attività'

@admin.register(Richiedente)
class RichiedenteAdmin(admin.ModelAdmin):
    list_display = ['nome_completo', 'email', 'cliente', 'attivo', 'num_attivita', 'created_at']
    list_filter = ['attivo', 'cliente', 'created_at']
    search_fields = ['nome', 'cognome', 'email']
    list_per_page = 25
    ordering = ['cognome', 'nome']
    
    fieldsets = (
        ('Informazioni Personali', {
            'fields': ('nome', 'cognome', 'email', 'telefono')
        }),
        ('Associazioni', {
            'fields': ('cliente', 'attivo')
        }),
    )
    
    def nome_completo(self, obj):
        return f"{obj.nome} {obj.cognome}"
    nome_completo.short_description = 'Nome Completo'
    nome_completo.admin_order_field = 'cognome'
    
    def num_attivita(self, obj):
        count = obj.attivita.count()
        if count > 0:
            url = reverse('admin:activities_attivita_changelist') + f'?richiedente__id__exact={obj.id}'
            return format_html('<a href="{}">{} attività</a>', url, count)
        return '0 attività'
    num_attivita.short_description = 'Attività'

class AllegatoAttivitaInline(admin.TabularInline):
    model = AllegatoAttivita
    extra = 0
    readonly_fields = ['nome_originale', 'dimensione_formattata', 'tipo_mime', 'caricato_il']
    fields = ['file', 'descrizione', 'nome_originale', 'dimensione_formattata', 'tipo_mime', 'caricato_il']
    
    def dimensione_formattata(self, obj):
        if obj.dimensione:
            return obj.dimensione_formattata
        return '-'
    dimensione_formattata.short_description = 'Dimensione'

@admin.register(Attivita)
class AttivitaAdmin(admin.ModelAdmin):
    list_display = ['nome_flusso', 'richiedente_link', 'cliente_badge', 'categoria_badge', 'stato_badge', 'allegati_count', 'data_creazione', 'data_chiusura']
    list_filter = ['stato', 'richiedente__cliente', 'categoria', 'data_creazione']
    search_fields = ['nome_flusso', 'richiedente__nome', 'richiedente__cognome', 'descrizione']
    list_per_page = 25
    date_hierarchy = 'data_creazione'
    ordering = ['-data_creazione']
    inlines = [AllegatoAttivitaInline]
    
    fieldsets = (
        ('Informazioni Generali', {
            'fields': ('nome_flusso', 'richiedente', 'categoria', 'stato')
        }),
        ('Descrizione e Note', {
            'fields': ('descrizione', 'note'),
            'classes': ('collapse',)
        }),
        ('Date', {
            'fields': ('data_chiusura',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['data_creazione', 'created_at', 'updated_at']
    
    def richiedente_link(self, obj):
        url = reverse('admin:activities_richiedente_change', args=[obj.richiedente.id])
        return format_html('<a href="{}">{}</a>', url, obj.richiedente.nome_completo)
    richiedente_link.short_description = 'Richiedente'
    richiedente_link.admin_order_field = 'richiedente__cognome'
    
    def cliente_badge(self, obj):
        cliente = obj.richiedente.cliente
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            cliente.colore_sfondo or '#6c757d',
            cliente.colore_testo or '#fff',
            cliente.nome
        )
    cliente_badge.short_description = 'Cliente'
    cliente_badge.admin_order_field = 'richiedente__cliente__nome'
    
    def categoria_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;"><i class="{}"></i> {}</span>',
            obj.categoria.colore,
            obj.categoria.icona,
            obj.categoria.nome
        )
    categoria_badge.short_description = 'Categoria'
    categoria_badge.admin_order_field = 'categoria__nome'
    
    def stato_badge(self, obj):
        if obj.is_aperta:
            return format_html('<span style="color: green; font-weight: bold;">● Aperta</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">● Chiusa</span>')
    stato_badge.short_description = 'Stato'
    stato_badge.admin_order_field = 'stato'
    
    def allegati_count(self, obj):
        count = obj.allegati_count
        if count > 0:
            return format_html('<span style="color: blue; font-weight: bold;">{} file</span>', count)
        return '0 file'
    allegati_count.short_description = 'Allegati'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('richiedente', 'richiedente__cliente', 'categoria').prefetch_related('allegati')
    
    actions = ['chiudi_attivita_selezionate', 'riapri_attivita_selezionate']
    
    def chiudi_attivita_selezionate(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(stato='aperta').update(
            stato='chiusa',
            data_chiusura=timezone.now()
        )
        self.message_user(request, f'{updated} attività sono state chiuse.')
    chiudi_attivita_selezionate.short_description = "Chiudi le attività selezionate"
    
    def riapri_attivita_selezionate(self, request, queryset):
        updated = queryset.filter(stato='chiusa').update(
            stato='aperta',
            data_chiusura=None
        )
        self.message_user(request, f'{updated} attività sono state riaperte.')
    riapri_attivita_selezionate.short_description = "Riapri le attività selezionate"

@admin.register(AllegatoAttivita)
class AllegatoAttivitaAdmin(admin.ModelAdmin):
    list_display = ['nome_originale', 'attivita_link', 'icona_file_display', 'dimensione_formattata', 'caricato_il']
    list_filter = ['tipo_mime', 'caricato_il']
    search_fields = ['nome_originale', 'descrizione', 'attivita__nome_flusso']
    list_per_page = 25
    ordering = ['-caricato_il']
    
    fieldsets = (
        ('File', {
            'fields': ('file', 'descrizione')
        }),
        ('Metadata (auto)', {
            'fields': ('nome_originale', 'dimensione', 'tipo_mime'),
            'classes': ('collapse',)
        }),
        ('Associazione', {
            'fields': ('attivita',)
        }),
    )
    
    readonly_fields = ['nome_originale', 'dimensione', 'tipo_mime']
    
    def attivita_link(self, obj):
        url = reverse('admin:activities_attivita_change', args=[obj.attivita.id])
        return format_html('<a href="{}">{}</a>', url, obj.attivita.nome_flusso)
    attivita_link.short_description = 'Attività'
    attivita_link.admin_order_field = 'attivita__nome_flusso'
    
    def icona_file_display(self, obj):
        return format_html('<i class="{}"></i>', obj.icona_file)
    icona_file_display.short_description = 'Tipo'

# Personalizzazione dell'interfaccia admin
admin.site.site_header = "Gestione Attività - Pannello Amministrativo"
admin.site.site_title = "Admin Attività"
admin.site.index_title = "Benvenuto nel pannello di amministrazione delle attività"