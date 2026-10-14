from django.shortcuts import render
from django.http import JsonResponse
from datetime import date, datetime, timedelta
from calendario.models import Evento
from .models import Cliente
from procedura.models import Procedura, Step, Ambiente, Tipologia
from activities.models import Attivita
from errors.models import Errore
from todo.models import Task
from django.db.models import Count, Q
from django.utils import timezone

def homepage(request):
    utente = request.user
    oggi = timezone.localdate()
    ora_attuale = timezone.now()

    # Eventi (solo i miei)
    miei_eventi = Evento.objects.filter(owner=utente, archived=False)
    eventi_oggi = miei_eventi.filter(
        data_inizio__date=oggi
    ).select_related('cliente').order_by('data_inizio')
    prossimi_eventi = miei_eventi.filter(
        data_inizio__date__gt=oggi,
        data_inizio__date__lte=oggi + timedelta(days=7),
    ).select_related('cliente').order_by('data_inizio')[:6]
    urgent_events = miei_eventi.filter(
        data_inizio__gte=ora_attuale,
        data_inizio__lte=ora_attuale + timedelta(hours=2),
    ).count()

    # To-do da fare: quelli di oggi e quelli rimasti indietro
    task_da_fare = Task.objects.filter(
        owner=utente, completed=False, archiviato=False, data_creazione__lte=oggi
    )
    # Attivita' aperte
    attivita_aperte = Attivita.objects.filter(owner=utente, stato='aperta')
    # Errori
    miei_errori = Errore.objects.filter(owner=utente)

    context = {
        'today': oggi,
        'eventi_oggi': eventi_oggi,
        'prossimi_eventi': prossimi_eventi,
        'urgent_events': urgent_events,
        'task_da_fare': task_da_fare.select_related('cliente', 'attivita').order_by('data_creazione', 'id')[:8],
        'totale_task_da_fare': task_da_fare.count(),
        'task_in_ritardo': task_da_fare.filter(data_creazione__lt=oggi).count(),
        'attivita_aperte': attivita_aperte.select_related(
            'richiedente', 'richiedente__cliente', 'categoria'
        ).order_by('-data_creazione')[:6],
        'totale_attivita_aperte': attivita_aperte.count(),
        'errori_recenti': miei_errori.select_related('cliente').order_by('-data', '-id')[:5],
        'totale_errori': miei_errori.count(),
        'recent_procedures': Procedura.objects.select_related(
            'ambiente', 'cliente', 'tipologia'
        ).annotate(num_step=Count('steps')).order_by('-id')[:5],
    }
    return render(request, 'homepage.html', context)


def get_dashboard_stats(request):
    """
    Vista API per ottenere statistiche aggiornate via AJAX
    """
    oggi = date.today()
    
    stats = {
        'events_today': Evento.objects.filter(
            owner=request.user,
            data_inizio__date=oggi, archived=False
        ).count(),
        'total_procedures': Procedura.objects.count(),
        'total_steps': Step.objects.count(),
        'urgent_events': Evento.objects.filter(
            owner=request.user,
            data_inizio__lte=timezone.now() + timedelta(hours=2),
            data_inizio__gte=timezone.now(),
            archived=False
        ).count()
    }
    
    return JsonResponse(stats)


def search_global(request):
    """
    Ricerca globale tra procedure, step ed eventi
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'results': []})
    
    results = []
    
    # Cerca nelle procedure
    procedures = Procedura.objects.filter(
        Q(nome__icontains=query) |
        Q(ambiente__nome__icontains=query) |
        Q(cliente__nome__icontains=query) |
        Q(tipologia__nome__icontains=query)
    ).select_related('ambiente', 'cliente', 'tipologia')[:5]
    
    for proc in procedures:
        results.append({
            'type': 'procedure',
            'title': proc.nome,
            'subtitle': f"{proc.ambiente.nome} - {proc.cliente.nome}",
            'url': f'/procedura/{proc.pk}/',
            'icon': 'bi-folder'
        })
    
    # Cerca negli step
    steps = Step.objects.filter(
        Q(titolo__icontains=query) |
        Q(corpo__icontains=query)
    ).select_related('procedura')[:5]
    
    for step in steps:
        results.append({
            'type': 'step',
            'title': step.titolo,
            'subtitle': f"Procedura: {step.procedura.nome}",
            'url': f'/step/{step.pk}/',
            'icon': 'bi-list-check'
        })
    
    # Cerca negli eventi
    events = Evento.objects.filter(
        Q(titolo__icontains=query) |
        Q(descrizione__icontains=query),
        owner=request.user,
        archived=False
    ).select_related('cliente')[:5]
    
    for event in events:
        results.append({
            'type': 'event',
            'title': event.titolo,
            'subtitle': f"Data: {event.data_inizio.strftime('%d/%m/%Y %H:%M')}",
            'url': f'/calendario/evento/{event.pk}/',
            'icon': 'bi-calendar-event'
        })
    
    return JsonResponse({'results': results})


def quick_stats_widget(request):
    """
    Widget per statistiche rapide da includere in altre pagine
    """
    oggi = date.today()
    
    context = {
        'events_today': Evento.objects.filter(
            owner=request.user,
            data_inizio__date=oggi, archived=False
        ).count(),
        'procedures_count': Procedura.objects.count(),
        'urgent_notifications': Evento.objects.filter(
            owner=request.user,
            data_inizio__lte=timezone.now() + timedelta(hours=1),
            data_inizio__gte=timezone.now(),
            archived=False
        ).count()
    }
    
    return render(request, 'widgets/quick_stats.html', context)