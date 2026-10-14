from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Procedura, Step

from core.mixins import SoloMieiMixin

# CRUD per Procedura
class ProceduraListView(ListView):
    model = Procedura
    template_name = "procedure/procedura_list.html"
    context_object_name = "procedure"

from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView
from .models import Procedura, Step

# Dettaglio della Procedura con gli Step associati
class ProceduraDetailView(DetailView):
    model = Procedura
    template_name = "procedure/procedura_detail.html"
    context_object_name = "procedura"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Aggiungi gli step associati alla procedura
        context['steps'] = Step.objects.filter(procedura=self.object)
        return context


class ProceduraCreateView(CreateView):
    model = Procedura
    template_name = "procedure/procedura_form.html"
    fields = ['nome', 'ambiente', 'cliente', 'tipologia']
    success_url = reverse_lazy('procedura-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class ProceduraUpdateView(SoloMieiMixin, UpdateView):
    model = Procedura
    template_name = "procedure/procedura_form.html"
    fields = ['nome', 'ambiente', 'cliente', 'tipologia']
    success_url = reverse_lazy('procedura-list')

class ProceduraDeleteView(SoloMieiMixin, DeleteView):
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
        # Tutti gli step della procedura, nell'ordine scelto dall'utente
        steps = list(Step.objects.filter(procedura=step.procedura).order_by('ordine', 'id'))
        index = steps.index(step)
        context['previous_step'] = steps[index - 1] if index > 0 else None
        context['next_step'] = steps[index + 1] if index < len(steps) - 1 else None
        context['current_position'] = index + 1
        context['total_steps'] = len(steps)
        return context

from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Procedura, Step

from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Procedura, Step

class StepCreateView(CreateView):
    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Procedura, pk=kwargs.get('procedura_id'), owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    model = Step
    template_name = "procedure/step_form.html"
    fields = ['titolo', 'corpo', 'immagini']  # Rimosso 'procedura' perché lo assegniamo manualmente

    def form_valid(self, form):
        procedura = get_object_or_404(Procedura, pk=self.kwargs.get('procedura_id'))
        form.instance.procedura = procedura  # Assegna l'istanza della Procedura
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('procedura-detail', kwargs={'pk': self.object.procedura.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['procedura_id'] = self.kwargs.get('procedura_id')  # Passa l'ID al template
        return context


class SoloMieiStepMixin:
    """Gli step si toccano solo se la loro procedura è dell'utente."""

    def get_queryset(self):
        return super().get_queryset().filter(procedura__owner=self.request.user)


class StepUpdateView(SoloMieiStepMixin, UpdateView):
    model = Step
    template_name = "procedure/step_form.html"
    fields = ['procedura', 'titolo', 'corpo', 'immagini']
    success_url = reverse_lazy('step-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # non si può spostare uno step in una procedura altrui
        form.fields['procedura'].queryset = Procedura.objects.filter(owner=self.request.user)
        return form

class StepDeleteView(SoloMieiStepMixin, DeleteView):
    model = Step
    template_name = "procedure/step_confirm_delete.html"
    success_url = reverse_lazy('step-list')


# API per il riordino degli step (drag and drop)
import json
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@require_POST
def update_step_order(request):
    """Salva il nuovo ordine degli step. Riceve {"step_order": [id, id, ...]}."""
    try:
        data = json.loads(request.body)
        step_ids = [int(i) for i in data.get("step_order", [])]
    except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
        return JsonResponse({"status": "error", "message": "Dati non validi"}, status=400)

    steps = Step.objects.filter(procedura__owner=request.user).in_bulk(step_ids)
    if not steps:
        return JsonResponse({"status": "error", "message": "Nessuno step trovato"}, status=400)

    with transaction.atomic():
        for index, step_id in enumerate(step_ids):
            step = steps.get(step_id)
            if step is not None and step.ordine != index:
                step.ordine = index
                step.save(update_fields=["ordine"])

    return JsonResponse({
        "status": "ok",
        "message": f"Aggiornati {len(steps)} step",
        "updated_count": len(steps),
    })
