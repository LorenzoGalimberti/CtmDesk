# calendario/views.py
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import ListView
from django.contrib import messages
from .models import Evento
from .forms import EventoForm

# Importa il modello Task dal todo
from todo.models import Task

def calendario_view(request):
    form = EventoForm()
    return render(request, 'calendario.html', {'form': form})

def eventi_json(request):
    """Ritorna gli eventi in formato JSON per FullCalendar"""
    eventi = Evento.objects.filter(archived=False)
    eventi_data = [evento.as_dict() for evento in eventi]
    return JsonResponse(eventi_data, safe=False)

def aggiungi_evento(request):
    """Crea un nuovo evento e automaticamente il task corrispondente nel todo"""
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            # Salva l'evento
            evento = form.save()
            
            # Crea automaticamente il task nel todo
            try:
                task = Task.objects.create(
                    title=f"📅 {evento.titolo}",
                    description=f"Evento programmato\n"
                               f"Descrizione: {evento.descrizione or 'Nessuna descrizione'}\n"
                               f"Inizio: {evento.data_inizio.strftime('%d/%m/%Y alle %H:%M')}\n"
                               f"Fine: {evento.data_fine.strftime('%d/%m/%Y alle %H:%M')}",
                    cliente=evento.cliente,
                    data_creazione=evento.data_inizio.date(),
                    completed=False,
                    archiviato=False
                )
                
                print(f"✅ Evento e task creati: {evento.titolo} - Task ID: {task.id}")
                
                # Ritorna i dati dell'evento per FullCalendar con info del task
                response_data = evento.as_dict()
                response_data['task_created'] = True
                response_data['task_id'] = task.id
                
                return JsonResponse(response_data)
                
            except Exception as e:
                print(f"❌ Errore nella creazione del task: {str(e)}")
                # Anche se il task fallisce, l'evento è comunque creato
                response_data = evento.as_dict()
                response_data['task_created'] = False
                response_data['task_error'] = str(e)
                
                return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'Dati non validi', 'form_errors': form.errors}, status=400)
    
    return JsonResponse({'error': 'Metodo non consentito'}, status=405)

def evento_dettaglio(request, event_id):
    evento = get_object_or_404(Evento, id=event_id)
    
    # Cerca se esiste un task collegato a questo evento
    task_collegato = Task.objects.filter(
        title__contains=evento.titolo,
        data_creazione=evento.data_inizio.date(),
        cliente=evento.cliente
    ).first()
    
    context = {
        'evento': evento,
        'task_collegato': task_collegato
    }
    
    return render(request, 'evento_dettaglio.html', context)

def elimina_evento(request, event_id):
    """Elimina l'evento e opzionalmente il task collegato"""
    if request.method == 'POST':
        evento = get_object_or_404(Evento, id=event_id)
        
        # Trova e elimina anche il task collegato se esiste
        task_collegato = Task.objects.filter(
            title__contains=evento.titolo,
            data_creazione=evento.data_inizio.date(),
            cliente=evento.cliente
        ).first()
        
        if task_collegato:
            task_collegato.delete()
            print(f"✅ Task collegato eliminato: {task_collegato.title}")
        
        evento.delete()
        messages.success(request, 'Evento e task collegato eliminati con successo!')
        return redirect('calendario')
    
    return redirect('calendario')

def archivia_evento(request, event_id):
    """Archivia l'evento e il task collegato"""
    evento = get_object_or_404(Evento, id=event_id)
    evento.archived = True
    evento.save()
    
    # Archivia anche il task collegato se esiste
    task_collegato = Task.objects.filter(
        title__contains=evento.titolo,
        data_creazione=evento.data_inizio.date(),
        cliente=evento.cliente
    ).first()
    
    if task_collegato and not task_collegato.archiviato:
        task_collegato.archive()  # Usa il metodo archive() del modello Task
        print(f"✅ Task collegato archiviato: {task_collegato.title}")
    
    messages.success(request, 'Evento e task collegato archiviati con successo!')
    return redirect('calendario')

class ListaEventiView(ListView):
    model = Evento
    template_name = 'lista_eventi.html'
    context_object_name = 'eventi'
    
    def get_queryset(self):
        archived = self.request.GET.get('archived', 'false') == 'true'
        return Evento.objects.filter(archived=archived)