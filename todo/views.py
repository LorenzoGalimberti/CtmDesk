# todo/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, datetime
from django.db.models import Q
from .models import Task
from .forms import TaskForm

def all_task(request):
    query = request.GET.get('q', '')
    tasks = Task.objects.all()
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) |
            Q(data_creazione__icontains=query) |
            Q(data_archiviazione__icontains=query)
        )
    return render(request, 'all_task.html', {'tasks': tasks, 'query': query})

from core.models import Cliente

def task_list(request):
    today = datetime.now().date()

    # Archivia automaticamente i task completati di giorni precedenti
    tasks_to_archive = Task.objects.filter(
        completed=True,
        archiviato=False,
        data_creazione__lt=today
    )
    for task in tasks_to_archive:
        task.archive()

    tasks = Task.objects.filter(archiviato=False, data_creazione__lte=today).order_by('data_creazione')

    # Filtra per cliente se il parametro GET è presente
    cliente_id = request.GET.get('cliente', None)
    if cliente_id:
        tasks = tasks.filter(cliente__id=cliente_id)

    # Filtra per tipo di task
    tipo_filter = request.GET.get('tipo', None)
    if tipo_filter in ['manual', 'activity']:
        tasks = tasks.filter(task_type=tipo_filter)

    # Prefetch delle relazioni per ottimizzare le query
    tasks = tasks.select_related('cliente', 'attivita')

    # Passa anche la lista dei clienti alla template
    clienti = Cliente.objects.all()

    form = TaskForm()
    return render(request, 'task_list.html', {
        'tasks': tasks, 
        'form': form, 
        'clienti': clienti
    })

def add_task(request):
    """Aggiunta task solo per quelli manuali"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            if not task.data_creazione:
                task.data_creazione = date.today()
            # I task creati manualmente sono sempre di tipo 'manual'
            task.task_type = 'manual'
            task.owner = request.user
            task.save()
            return redirect('todo:task_list')
    else:
        form = TaskForm()
    tasks = Task.objects.filter(archiviato=False).order_by('data_creazione')
    return render(request, 'task_list.html', {'tasks': tasks, 'form': form})

def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        old_status = task.completed
        task.completed = not task.completed
        task.save()
        
        # Se il task è collegato a un'attività e viene completato,
        # verifica se anche l'attività dovrebbe essere chiusa
        if task.attivita and task.completed:
            # Controlla se tutti i task dell'attività sono completati
            all_tasks_completed = not task.attivita.tasks.filter(
                completed=False, 
                archiviato=False
            ).exists()
            
            if all_tasks_completed and task.attivita.is_aperta:
                # Chiudi automaticamente l'attività
                task.attivita.chiudi_attivita()
                return JsonResponse({
                    'status': 'success', 
                    'completed': task.completed,
                    'activity_closed': True,
                    'activity_name': task.attivita.nome_flusso
                })
        
        return JsonResponse({'status': 'success', 'completed': task.completed})
    return JsonResponse({'status': 'error'})

def archive_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if not task.archiviato:
        task.archiviato = True
        task.data_archiviazione = timezone.now()
        task.save()
    return JsonResponse({
        'status': 'success', 
        'archiviato': True, 
        'data_archiviazione': task.data_archiviazione.strftime('%d %b %Y %H:%M')
    })

def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Impedisci l'eliminazione di task collegati ad attività
    if task.task_type == 'activity':
        return JsonResponse({
            'status': 'error',
            'message': 'I task collegati ad attività non possono essere eliminati direttamente.'
        })
    
    task.delete()
    return JsonResponse({'status': 'success'})

def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save(commit=False)
            
            # Per i task da attività, permetti solo la modifica di descrizione e cliente
            if task.task_type == 'activity':
                # Mantieni il titolo originale per i task da attività
                updated_task.title = task.title
                # Mantieni anche il tipo e l'attività collegata
                updated_task.task_type = task.task_type
                updated_task.attivita = task.attivita
            
            updated_task.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        # Richiesta GET per ottenere i dati del task
        data = {
            'id': task.id,
            'title': task.title,
            'description': task.description or '',
            'cliente_id': task.cliente.id if task.cliente else None,
            'cliente_nome': task.cliente.nome if task.cliente else 'Nessun cliente',
            'completed': task.completed,
            'task_type': task.task_type,
            'data_creazione': task.data_creazione.strftime('%Y-%m-%d') if task.data_creazione else '',
            'attivita_id': task.attivita.id if task.attivita else None,
            'attivita_nome': task.attivita.nome_flusso if task.attivita else None,
        }
        return JsonResponse(data)

def get_clienti(request):
    clienti = Cliente.objects.all()
    data = [{'id': cliente.id, 'nome': cliente.nome, 
            'colore_sfondo': cliente.colore_sfondo, 
            'colore_testo': cliente.colore_testo} 
            for cliente in clienti]
    return JsonResponse(data, safe=False)