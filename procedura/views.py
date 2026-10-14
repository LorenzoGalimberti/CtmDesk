from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Procedura, Step

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

from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Procedura, Step

from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Procedura, Step

class StepCreateView(CreateView):
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


class StepUpdateView(UpdateView):
    model = Step
    template_name = "procedure/step_form.html"
    fields = ['procedura', 'titolo', 'corpo', 'immagini']
    success_url = reverse_lazy('step-list')

class StepDeleteView(DeleteView):
    model = Step
    template_name = "procedure/step_confirm_delete.html"
    success_url = reverse_lazy('step-list')
