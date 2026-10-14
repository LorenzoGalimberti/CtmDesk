# activities/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
import os
from .models import Attivita, Richiedente, Categoria, AllegatoAttivita
from .forms import AttivitaForm, RichiedenteForm, CategoriaForm, AllegatoAttivitaForm

# Importa Task per creare task automatici
try:
    from todo.models import Task
    TASK_INTEGRATION_AVAILABLE = True
except ImportError:
    TASK_INTEGRATION_AVAILABLE = False

def create_task_from_activity(attivita):
    """Crea automaticamente un task to-do da un'attività"""
    if not TASK_INTEGRATION_AVAILABLE:
        return None
        
    try:
        from datetime import date
        
        # Crea il task
        task = Task.objects.create(
            title=f"Lavorare su: {attivita.nome_flusso}",
            description=f"Task automatico per l'attività: {attivita.nome_flusso}\n"
                       f"Richiedente: {attivita.richiedente.nome_completo}\n"
                       f"Categoria: {attivita.categoria.nome}\n"
                       f"Descrizione: {attivita.descrizione or 'Nessuna descrizione'}",
            cliente=attivita.richiedente.cliente,
            attivita=attivita,
            task_type='activity',
            data_creazione=date.today(),
            completed=False
        )
        return task
    except Exception as e:
        print(f"Errore nella creazione del task: {e}")
        return None

# CRUD per Attività
class AttivitaListView(ListView):
    model = Attivita
    template_name = "activities/attivita_list.html"
    context_object_name = "attivita"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Attivita.objects.select_related('richiedente', 'richiedente__cliente', 'categoria')
        
        # Filtro per stato
        stato_filter = self.request.GET.get('stato')
        if stato_filter in ['aperta', 'chiusa']:
            queryset = queryset.filter(stato=stato_filter)
        
        # Filtro per cliente
        cliente_filter = self.request.GET.get('cliente')
        if cliente_filter:
            queryset = queryset.filter(richiedente__cliente_id=cliente_filter)
            
        # Filtro per categoria
        categoria_filter = self.request.GET.get('categoria')
        if categoria_filter:
            queryset = queryset.filter(categoria_id=categoria_filter)
        
        # Ricerca
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome_flusso__icontains=search) |
                Q(richiedente__nome__icontains=search) |
                Q(richiedente__cognome__icontains=search) |
                Q(descrizione__icontains=search) |
                Q(categoria__nome__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Cliente
        context['clienti'] = Cliente.objects.all()
        context['categorie'] = Categoria.objects.filter(attiva=True)
        context['stato_selected'] = self.request.GET.get('stato', '')
        context['cliente_selected'] = self.request.GET.get('cliente', '')
        context['categoria_selected'] = self.request.GET.get('categoria', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context

class AttivitaDetailView(DetailView):
    model = Attivita
    template_name = "activities/attivita_detail.html"
    context_object_name = "attivita"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Allegati
        if hasattr(self.object, 'allegati'):
            context['allegati'] = self.object.allegati.all()
        context['allegato_form'] = AllegatoAttivitaForm()
        
        # Task collegati con prefetch per ottimizzare le query
        if TASK_INTEGRATION_AVAILABLE:
            context['tasks_collegati'] = self.object.tasks.select_related('cliente').all()
            
            # Statistiche task alternative (se i metodi del modello non funzionano)
            tasks = self.object.tasks.all()
            context['task_stats'] = {
                'totali': tasks.count(),
                'completati': tasks.filter(completed=True).count(),
                'in_corso': tasks.filter(completed=False, archiviato=False).count(),
                'archiviati': tasks.filter(archiviato=True).count(),
            }
            
            # Calcola percentuale di completamento
            if context['task_stats']['totali'] > 0:
                context['task_stats']['percentuale'] = round(
                    (context['task_stats']['completati'] / context['task_stats']['totali']) * 100
                )
            else:
                context['task_stats']['percentuale'] = 0
        else:
            context['tasks_collegati'] = []
            context['task_stats'] = {
                'totali': 0, 'completati': 0, 'in_corso': 0, 'archiviati': 0, 'percentuale': 0
            }
            
        return context

class AttivitaCreateView(CreateView):
    model = Attivita
    form_class = AttivitaForm
    template_name = "activities/attivita_form.html"
    success_url = reverse_lazy('attivita-list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Crea automaticamente un task to-do per questa attività
        if self.object.stato == 'aperta' and TASK_INTEGRATION_AVAILABLE:
            task = create_task_from_activity(self.object)
            if task:
                messages.success(
                    self.request, 
                    f'Attività creata con successo! È stato creato anche un task to-do: "{task.title}"'
                )
            else:
                messages.success(self.request, 'Attività creata con successo!')
                messages.warning(self.request, 'Non è stato possibile creare il task to-do automatico.')
        else:
            messages.success(self.request, 'Attività creata con successo!')
        
        return response

class AttivitaUpdateView(UpdateView):
    model = Attivita
    form_class = AttivitaForm
    template_name = "activities/attivita_form.html"
    success_url = reverse_lazy('attivita-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Attività aggiornata con successo!')
        return super().form_valid(form)

class AttivitaDeleteView(DeleteView):
    model = Attivita
    template_name = "activities/attivita_confirm_delete.html"
    success_url = reverse_lazy('attivita-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Attività eliminata con successo!')
        return super().delete(request, *args, **kwargs)

# Views per azioni specifiche
def chiudi_attivita(request, pk):
    """Vista per chiudere un'attività"""
    attivita = get_object_or_404(Attivita, pk=pk)
    if hasattr(attivita, 'is_aperta') and attivita.is_aperta:
        attivita.chiudi_attivita()
        
        # Completa automaticamente i task associati
        if TASK_INTEGRATION_AVAILABLE:
            Task.objects.filter(attivita=attivita, completed=False).update(completed=True)
            messages.success(request, f'Attività "{attivita.nome_flusso}" chiusa con successo! Anche i task associati sono stati completati.')
        else:
            messages.success(request, f'Attività "{attivita.nome_flusso}" chiusa con successo!')
    else:
        messages.warning(request, 'L\'attività è già chiusa.')
    return redirect('attivita-detail', pk=pk)

def riapri_attivita(request, pk):
    """Vista per riaprire un'attività"""
    attivita = get_object_or_404(Attivita, pk=pk)
    if hasattr(attivita, 'is_chiusa') and attivita.is_chiusa:
        attivita.riapri_attivita()
        
        if TASK_INTEGRATION_AVAILABLE:
            # Riapri anche i task associati se non sono archiviati
            Task.objects.filter(
                attivita=attivita, 
                completed=True, 
                archiviato=False
            ).update(completed=False)
            
            # Crea un nuovo task se non esistono task aperti per questa attività
            existing_open_tasks = Task.objects.filter(
                attivita=attivita, 
                completed=False, 
                archiviato=False
            ).count()
            
            if existing_open_tasks == 0:
                task = create_task_from_activity(attivita)
                if task:
                    messages.success(
                        request, 
                        f'Attività "{attivita.nome_flusso}" riaperta con successo! È stato creato un nuovo task to-do.'
                    )
                else:
                    messages.success(request, f'Attività "{attivita.nome_flusso}" riaperta con successo!')
            else:
                messages.success(request, f'Attività "{attivita.nome_flusso}" riaperta con successo!')
        else:
            messages.success(request, f'Attività "{attivita.nome_flusso}" riaperta con successo!')
    else:
        messages.warning(request, 'L\'attività è già aperta.')
    return redirect('attivita-detail', pk=pk)

# Views per Allegati
@require_POST
def carica_allegato(request, attivita_id):
    """Vista per caricare un allegato per un'attività"""
    attivita = get_object_or_404(Attivita, id=attivita_id)
    
    if 'file' not in request.FILES:
        messages.error(request, 'Nessun file selezionato.')
        return redirect('attivita-detail', pk=attivita_id)
    
    form = AllegatoAttivitaForm(request.POST, request.FILES)
    if form.is_valid():
        allegato = form.save(commit=False)
        allegato.attivita = attivita
        allegato.save()
        messages.success(request, f'File "{allegato.nome_originale}" caricato con successo!')
    else:
        messages.error(request, 'Errore nel caricamento del file.')
    
    return redirect('attivita-detail', pk=attivita_id)

def scarica_allegato(request, allegato_id):
    """Vista per scaricare un allegato"""
    allegato = get_object_or_404(AllegatoAttivita, id=allegato_id)
    
    if not os.path.exists(allegato.file.path):
        raise Http404("File non trovato")
    
    with open(allegato.file.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=allegato.tipo_mime)
        response['Content-Disposition'] = f'attachment; filename="{allegato.nome_originale}"'
        return response

def anteprima_allegato(request, allegato_id):
    """Vista per visualizzare l'anteprima di un allegato"""
    allegato = get_object_or_404(AllegatoAttivita, id=allegato_id)
    
    if not os.path.exists(allegato.file.path):
        raise Http404("File non trovato")
    
    # Per le immagini, restituisci direttamente il file
    if allegato.is_image:
        with open(allegato.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=allegato.tipo_mime)
            response['Content-Disposition'] = f'inline; filename="{allegato.nome_originale}"'
            return response
    
    # Per i PDF, restituisci per visualizzazione inline
    elif allegato.is_pdf:
        with open(allegato.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{allegato.nome_originale}"'
            return response
    
    # Per i file di testo, mostra il contenuto
    elif allegato.is_text:
        try:
            with open(allegato.file.path, 'r', encoding='utf-8') as f:
                contenuto = f.read()
        except UnicodeDecodeError:
            try:
                with open(allegato.file.path, 'r', encoding='latin-1') as f:
                    contenuto = f.read()
            except:
                contenuto = "Errore nella lettura del file. Encoding non supportato."
        
        context = {
            'allegato': allegato,
            'contenuto': contenuto,
            'attivita': allegato.attivita
        }
        return render(request, 'activities/anteprima_testo.html', context)
    
    # Per documenti Office, crea una pagina di anteprima con link per aprire
    elif allegato.is_office_document:
        context = {
            'allegato': allegato,
            'attivita': allegato.attivita,
            'tipo_documento': 'office'
        }
        return render(request, 'activities/anteprima_documento.html', context)
    
    else:
        context = {
            'allegato': allegato,
            'attivita': allegato.attivita,
            'tipo_documento': 'altro'
        }
        return render(request, 'activities/anteprima_documento.html', context)

def elimina_allegato(request, allegato_id):
    """Vista per eliminare un allegato"""
    allegato = get_object_or_404(AllegatoAttivita, id=allegato_id)
    attivita_id = allegato.attivita.id
    nome_file = allegato.nome_originale
    
    allegato.delete()
    messages.success(request, f'File "{nome_file}" eliminato con successo!')
    
    return redirect('attivita-detail', pk=attivita_id)

# CRUD per Categorie
class CategoriaListView(ListView):
    model = Categoria
    template_name = "activities/categoria_list.html"
    context_object_name = "categorie"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Categoria.objects.prefetch_related('attivita')
        
        # Filtro per attive/non attive
        attiva_filter = self.request.GET.get('attiva')
        if attiva_filter == 'true':
            queryset = queryset.filter(attiva=True)
        elif attiva_filter == 'false':
            queryset = queryset.filter(attiva=False)
        
        # Ricerca
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) |
                Q(descrizione__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attiva_selected'] = self.request.GET.get('attiva', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context

class CategoriaDetailView(DetailView):
    model = Categoria
    template_name = "activities/categoria_detail.html"
    context_object_name = "categoria"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attivita_recenti'] = self.object.attivita.all()[:10]
        return context

class CategoriaCreateView(CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "activities/categoria_form.html"
    success_url = reverse_lazy('categoria-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Categoria creata con successo!')
        return super().form_valid(form)

class CategoriaUpdateView(UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "activities/categoria_form.html"
    success_url = reverse_lazy('categoria-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Categoria aggiornata con successo!')
        return super().form_valid(form)

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = "activities/categoria_confirm_delete.html"
    success_url = reverse_lazy('categoria-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Categoria eliminata con successo!')
        return super().delete(request, *args, **kwargs)

# CRUD per Richiedenti
class RichiedenteListView(ListView):
    model = Richiedente
    template_name = "activities/richiedente_list.html"
    context_object_name = "richiedenti"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Richiedente.objects.select_related('cliente').prefetch_related('attivita')
        
        # Filtro per cliente
        cliente_filter = self.request.GET.get('cliente')
        if cliente_filter:
            queryset = queryset.filter(cliente_id=cliente_filter)
        
        # Filtro per attivi/non attivi
        attivo_filter = self.request.GET.get('attivo')
        if attivo_filter == 'true':
            queryset = queryset.filter(attivo=True)
        elif attivo_filter == 'false':
            queryset = queryset.filter(attivo=False)
        
        # Ricerca
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) |
                Q(cognome__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Cliente
        
        context['clienti'] = Cliente.objects.all()
        context['cliente_selected'] = self.request.GET.get('cliente', '')
        context['attivo_selected'] = self.request.GET.get('attivo', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Statistiche per le card
        all_richiedenti = Richiedente.objects.all()
        context['richiedenti_attivi'] = all_richiedenti.filter(attivo=True).count()
        context['richiedenti_con_attivita'] = all_richiedenti.filter(attivita__isnull=False).distinct().count()
        
        # Gestisci il caso in cui created_at potrebbe non esistere
        if hasattr(Richiedente, 'created_at'):
            context['richiedenti_oggi'] = all_richiedenti.filter(created_at__date=timezone.now().date()).count()
        else:
            context['richiedenti_oggi'] = 0
        
        return context

class RichiedenteDetailView(DetailView):
    model = Richiedente
    template_name = "activities/richiedente_detail.html"
    context_object_name = "richiedente"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attivita_recenti'] = self.object.attivita.all()[:10]
        return context

class RichiedenteCreateView(CreateView):
    model = Richiedente
    form_class = RichiedenteForm
    template_name = "activities/richiedente_form.html"
    success_url = reverse_lazy('richiedente-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Richiedente creato con successo!')
        return super().form_valid(form)

class RichiedenteUpdateView(UpdateView):
    model = Richiedente
    form_class = RichiedenteForm
    template_name = "activities/richiedente_form.html"
    success_url = reverse_lazy('richiedente-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Richiedente aggiornato con successo!')
        return super().form_valid(form)

class RichiedenteDeleteView(DeleteView):
    model = Richiedente
    template_name = "activities/richiedente_confirm_delete.html"
    success_url = reverse_lazy('richiedente-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Richiedente eliminato con successo!')
        return super().delete(request, *args, **kwargs)

def dashboard_activities(request):
    """Dashboard per visualizzare statistiche delle attività"""
    from core.models import Cliente
    
    context = {
        'totale_attivita': Attivita.objects.count(),
        'attivita_aperte': Attivita.objects.filter(stato='aperta').count(),
        'attivita_chiuse': Attivita.objects.filter(stato='chiusa').count(),
        'totale_richiedenti': Richiedente.objects.filter(attivo=True).count(),
        'totale_categorie': Categoria.objects.filter(attiva=True).count(),
        'attivita_per_cliente': Cliente.objects.annotate(
            num_attivita=Count('richiedenti__attivita')
        ).order_by('-num_attivita')[:5],
        'attivita_per_categoria': Categoria.objects.annotate(
            num_attivita=Count('attivita')
        ).filter(attiva=True).order_by('-num_attivita')[:5],
        'attivita_recenti': Attivita.objects.select_related(
            'richiedente', 'richiedente__cliente', 'categoria'
        ).order_by('-data_creazione')[:10]
    }
    
    return render(request, 'activities/dashboard.html', context)