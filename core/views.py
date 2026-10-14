from django.shortcuts import render
from django.http import JsonResponse
from datetime import date, datetime, timedelta
from calendario.models import Evento
from .models import Cliente
from procedura.models import Procedura, Step, Ambiente, Tipologia
from django.db.models import Count, Q
from django.utils import timezone

def homepage(request):
    # Data corrente
    oggi = date.today()
    ora_attuale = timezone.now()
    
    # Eventi di oggi
    eventi_oggi = Evento.objects.filter(
        owner=request.user,
        data_inizio__date=oggi,
        archived=False
    ).select_related('cliente').order_by('data_inizio')
    
    # Prossimi eventi della settimana (escluso oggi)
    fine_settimana = oggi + timedelta(days=7)
    prossimi_eventi = Evento.objects.filter(
        owner=request.user,
        data_inizio__date__gt=oggi,
        data_inizio__date__lte=fine_settimana,
        archived=False
    ).select_related('cliente').order_by('data_inizio')[:6]
    
    # Eventi urgenti (che iniziano tra meno di 2 ore)
    tra_due_ore = ora_attuale + timedelta(hours=2)
    urgent_events = Evento.objects.filter(
        owner=request.user,
        data_inizio__lte=tra_due_ore,
        data_inizio__gte=ora_attuale,
        archived=False
    ).count()
    
    # Statistiche generali
    total_procedures = Procedura.objects.count()
    total_events_today = eventi_oggi.count()
    total_steps = Step.objects.count()
    
    # Clienti (tabella unica in core)
    total_clients = Cliente.objects.count()
    
    # Procedure recenti (ultime 5 create/modificate)
    recent_procedures = Procedura.objects.select_related(
        'ambiente', 'cliente', 'tipologia'
    ).prefetch_related('steps').order_by('-id')[:5]
    
    # Statistiche aggiuntive per insights
    procedures_by_environment = Procedura.objects.values(
        'ambiente__nome'
    ).annotate(count=Count('id')).order_by('-count')[:3]
    
    procedures_by_client = Procedura.objects.values(
        'cliente__nome'
    ).annotate(count=Count('id')).order_by('-count')[:3]
    
    # Eventi per cliente (top 3)
    events_by_client = Evento.objects.filter(
        owner=request.user,
        archived=False
    ).values('cliente__nome').annotate(
        count=Count('id')
    ).order_by('-count')[:3]
    
    context = {
        'today': oggi,
        'eventi_oggi': eventi_oggi,
        'prossimi_eventi': prossimi_eventi,
        'urgent_events': urgent_events,
        'total_procedures': total_procedures,
        'total_events_today': total_events_today,
        'total_clients': total_clients,
        'total_steps': total_steps,
        'recent_procedures': recent_procedures,
        'procedures_by_environment': procedures_by_environment,
        'procedures_by_client': procedures_by_client,
        'events_by_client': events_by_client,
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