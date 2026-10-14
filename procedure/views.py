from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
# Importa i modelli dall'app corretta "procedura" (non "procedure")
from procedura.models import Procedura, Step

# CRUD per Procedura
class ProceduraListView(ListView):
    model = Procedura
    template_name = "procedure/procedura_list.html"
    context_object_name = "procedure"

class ProceduraDetailView(DetailView):
    model = Procedura
    template_name = "procedure/procedura_detail.html"
    context_object_name = "procedura"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ottieni gli step per questa procedura dall'app "procedura"
        steps = self.object.steps.all().order_by('ordine', 'id')
        
        # Controlla se tutti gli step hanno ordine 0 (problema comune)
        steps_with_zero_order = steps.filter(ordine=0).count()
        total_steps = steps.count()
        
        # Se tutti gli step hanno ordine 0, sistemali automaticamente
        if total_steps > 1 and steps_with_zero_order == total_steps:
            print(f"🔧 Sistemando automaticamente {total_steps} step per la procedura '{self.object.nome}'")
            for index, step in enumerate(steps.order_by('id')):  # Ordina per ID (cronologico)
                step.ordine = index
                step.save()
                print(f"   ✅ Step '{step.titolo}' → ordine {index}")
            
            # Ricarica gli step con il nuovo ordine
            steps = self.object.steps.all().order_by('ordine')
            context['order_fixed'] = True
            context['fixed_count'] = total_steps
        else:
            context['order_fixed'] = False
        
        context['steps'] = steps
        return context

class ProceduraCreateView(CreateView):
    model = Procedura
    template_name = "procedure/procedura_form.html"
    fields = ['nome', 'ambiente', 'cliente', 'tipologia']
    success_url = reverse_lazy('procedura-list')

class ProceduraUpdateView(UpdateView):
    model = Procedura
    template_name = "procedure/procedura_form.html"
    fields = ['nome', 'ambiente', 'cliente', 'tipologia']
    success_url = reverse_lazy('procedura-list')

class ProceduraDeleteView(DeleteView):
    model = Procedura
    template_name = "procedure/procedura_confirm_delete.html"
    success_url = reverse_lazy('procedura-list')

# CRUD per Step
class StepListView(ListView):
    model = Step
    template_name = "procedure/step_list.html"
    context_object_name = "steps"

class StepDetailView(DetailView):
    model = Step
    template_name = "procedure/step_detail.html"
    context_object_name = "step"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = self.object
        
        # SE questo step ha ordine 0, sistemiamo TUTTI gli step della procedura
        if step.ordine == 0:
            all_steps = step.procedura.steps.all().order_by('id')  # Ordina per ID (cronologico)
            for index, s in enumerate(all_steps):
                if s.ordine != index:
                    s.ordine = index
                    s.save()
            
            # Ricarica lo step corrente con il nuovo ordine
            step.refresh_from_db()
        
        # Trova lo step precedente (stesso procedura, ordine minore, il più alto)
        previous_step = Step.objects.filter(
            procedura=step.procedura,
            ordine__lt=step.ordine
        ).order_by('-ordine').first()
        
        # Trova lo step successivo (stesso procedura, ordine maggiore, il più basso)  
        next_step = Step.objects.filter(
            procedura=step.procedura,
            ordine__gt=step.ordine
        ).order_by('ordine').first()
        
        context['previous_step'] = previous_step
        context['next_step'] = next_step
        
        # Aggiungi informazioni sulla posizione corrente
        all_steps_list = list(step.procedura.steps.all().order_by('ordine'))
        try:
            current_position = all_steps_list.index(step) + 1  # Posizione 1-based
            context['current_position'] = current_position
            context['total_steps'] = len(all_steps_list)
        except ValueError:
            context['current_position'] = 1
            context['total_steps'] = 1
        
        return context

class StepCreateView(CreateView):
    model = Step  # Ora usa procedura.models.Step
    template_name = "procedure/step_form.html"
    fields = ['titolo', 'corpo', 'immagini']  # Rimuovo procedura dai fields
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Se viene passato procedura_id nell'URL, pre-seleziona la procedura
        procedura_id = self.kwargs.get('procedura_id')
        if procedura_id:
            context['procedura_id'] = procedura_id
            try:
                procedura = Procedura.objects.get(id=procedura_id)
                context['procedura'] = procedura
            except Procedura.DoesNotExist:
                pass
        return context
    
    def form_valid(self, form):
        # Se viene passato procedura_id, assegnalo automaticamente
        procedura_id = self.kwargs.get('procedura_id')
        if procedura_id:
            try:
                procedura = Procedura.objects.get(id=procedura_id)
                form.instance.procedura = procedura
                
                # Assegna automaticamente l'ordine successivo
                from django.db.models import Max
                max_order = procedura.steps.aggregate(
                    max_order=Max('ordine')
                )['max_order']
                form.instance.ordine = (max_order or 0) + 1
                
            except Procedura.DoesNotExist:
                pass
        
        return super().form_valid(form)
    
    def get_success_url(self):
        procedura_id = self.kwargs.get('procedura_id')
        if procedura_id:
            return reverse_lazy('procedura-detail', kwargs={'pk': procedura_id})
        return reverse_lazy('step-list')

class StepUpdateView(UpdateView):
    model = Step  # Ora usa procedura.models.Step
    template_name = "procedure/step_form.html"
    fields = ['procedura', 'titolo', 'corpo', 'immagini']  # Includo procedura per permettere il cambio
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['procedura_id'] = self.object.procedura.id
        context['procedura'] = self.object.procedura
        return context
    
    def get_success_url(self):
        return reverse_lazy('step-detail', kwargs={'pk': self.object.pk})

class StepDeleteView(DeleteView):
    model = Step  # Ora usa procedura.models.Step
    template_name = "procedure/step_confirm_delete.html"
    
    def get_success_url(self):
        return reverse_lazy('procedura-detail', kwargs={'pk': self.object.procedura.pk})

#################################################
#                API
#################################################

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import models

# Vista per debug - mostra gli step di una procedura
def debug_steps(request, procedura_id):
    """Vista per debug - mostra tutti gli step di una procedura"""
    try:
        procedura = Procedura.objects.get(id=procedura_id)  # Usa procedura.models.Procedura
        steps = procedura.steps.all().order_by('ordine')
        
        debug_info = {
            "procedura_id": procedura_id,
            "procedura_nome": procedura.nome,
            "steps": [
                {
                    "id": step.id,
                    "titolo": step.titolo,
                    "ordine": step.ordine
                }
                for step in steps
            ]
        }
        
        return JsonResponse(debug_info)
    except Procedura.DoesNotExist:
        return JsonResponse({"error": "Procedura non trovata"}, status=404)

@require_POST
def update_step_order(request):
    try:
        # Leggi i dati JSON dalla richiesta
        data = json.loads(request.body)
        step_order = data.get("step_order", [])
        
        print("🔄 Nuovo ordine ricevuto:", step_order)
        print("🔄 Tipo degli ID ricevuti:", [type(id) for id in step_order])
        
        # Controlliamo TUTTI gli step nel database per vedere cosa c'è davvero
        all_steps = Step.objects.all().values_list('id', 'titolo', 'procedura__nome', 'procedura__id')  # Usa procedura.models.Step
        print("📋 TUTTI gli step nel database:", list(all_steps))
        
        # Controlliamo specificamente gli step richiesti
        existing_steps = Step.objects.filter(id__in=step_order)
        existing_ids = list(existing_steps.values_list('id', 'titolo', 'procedura__nome'))
        print("📋 Step richiesti che esistono nel DB:", existing_ids)
        
        # Controlliamo se qualche ID è di tipo diverso (string vs int)
        step_order_int = []
        for step_id in step_order:
            try:
                step_order_int.append(int(step_id))
            except (ValueError, TypeError):
                print(f"❌ ID non convertibile a int: {step_id} (tipo: {type(step_id)})")
                
        print("🔄 Ordine convertito a int:", step_order_int)
        
        # Riprova la query con gli ID convertiti
        existing_steps_int = Step.objects.filter(id__in=step_order_int)
        existing_ids_int = list(existing_steps_int.values_list('id', 'titolo', 'procedura__nome'))
        print("📋 Step trovati con ID convertiti:", existing_ids_int)
        
        if not existing_steps_int.exists():
            print("❌ Nessuno degli step richiesti esiste nel database dopo conversione!")
            return JsonResponse({
                "status": "error", 
                "message": f"Nessuno step trovato con gli ID: {step_order_int}",
                "debug_info": {
                    "received_ids": step_order,
                    "converted_ids": step_order_int,
                    "existing_steps": list(all_steps)
                }
            }, status=400)
        
        # Aggiorna l'ordine solo degli step che esistono
        success_count = 0
        for index, step_id in enumerate(step_order_int):
            try:
                step = Step.objects.get(id=step_id)
                old_order = step.ordine
                step.ordine = index
                step.save()
                print(f"   ✅ Step '{step.titolo}' - Ordine: {old_order} → {index}")
                success_count += 1
            except Step.DoesNotExist:
                print(f"   ❌ Step con ID {step_id} non trovato")
                continue
        
        print(f"🎉 Aggiornati {success_count} step con successo!")
        return JsonResponse({
            "status": "ok", 
            "message": f"Aggiornati {success_count} step",
            "updated_count": success_count
        })
        
    except json.JSONDecodeError:
        print("❌ Errore: JSON non valido")
        return JsonResponse({"status": "error", "message": "JSON non valido"}, status=400)
    except Exception as e:
        print(f"❌ Errore generico: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)}, status=400)