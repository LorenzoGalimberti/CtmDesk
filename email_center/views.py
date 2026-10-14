# email_integration/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone

from .models import EmailConfig, EmailLabel, ImportedEmail
from .forms import EmailConfigForm, EmailLabelForm, EmailImportForm
from .services import EmailService, EmailImportService

import logging
logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, ListView):
    """
    Dashboard principale per l'integrazione email.
    """
    template_name = 'email_integration/dashboard.html'
    context_object_name = 'email_configs'
    
    def get_queryset(self):
        return EmailConfig.objects.filter(user=self.request.user).order_by('-active', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'dashboard'
        return context

class EmailConfigCreateView(LoginRequiredMixin, CreateView):
    """
    Crea una nuova configurazione email.
    """
    model = EmailConfig
    form_class = EmailConfigForm
    template_name = 'email_integration/email_config_form.html'
    success_url = reverse_lazy('email_integration:dashboard')
    
    def form_valid(self, form):
        # Imposta l'utente corrente
        form.instance.user = self.request.user
        messages.success(self.request, 'Configurazione email creata con successo.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'email_config'
        context['title'] = 'Nuova Configurazione Email'
        return context

class EmailConfigUpdateView(LoginRequiredMixin, UpdateView):
    """
    Aggiorna una configurazione email esistente.
    """
    model = EmailConfig
    form_class = EmailConfigForm
    template_name = 'email_integration/email_config_form.html'
    success_url = reverse_lazy('email_integration:dashboard')
    
    def get_queryset(self):
        return EmailConfig.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Configurazione email aggiornata con successo.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'email_config'
        context['title'] = 'Modifica Configurazione Email'
        return context

class EmailConfigDeleteView(LoginRequiredMixin, DeleteView):
    """
    Elimina una configurazione email.
    """
    model = EmailConfig
    template_name = 'email_integration/email_config_confirm_delete.html'
    success_url = reverse_lazy('email_integration:dashboard')
    
    def get_queryset(self):
        return EmailConfig.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Configurazione email eliminata con successo.')
        return super().delete(request, *args, **kwargs)

class EmailLabelListView(LoginRequiredMixin, ListView):
    """
    Lista delle etichette email per una configurazione.
    """
    model = EmailLabel
    template_name = 'email_integration/email_label_list.html'
    context_object_name = 'labels'
    
    def get_queryset(self):
        self.config = get_object_or_404(EmailConfig, pk=self.kwargs['config_id'], user=self.request.user)
        return EmailLabel.objects.filter(config=self.config)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = self.config
        context['active_tab'] = 'email_config'
        return context

class EmailLabelCreateView(LoginRequiredMixin, CreateView):
    """
    Crea una nuova etichetta email.
    """
    model = EmailLabel
    form_class = EmailLabelForm
    template_name = 'email_integration/email_label_form.html'
    
    def get_success_url(self):
        return reverse_lazy('email_integration:email_label_list', kwargs={'config_id': self.kwargs['config_id']})
    
    def get_initial(self):
        initial = super().get_initial()
        self.config = get_object_or_404(EmailConfig, pk=self.kwargs['config_id'], user=self.request.user)
        return initial
    
    def form_valid(self, form):
        form.instance.config = self.config
        messages.success(self.request, 'Etichetta email creata con successo.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = self.config
        context['active_tab'] = 'email_config'
        context['title'] = 'Nuova Etichetta Email'
        
        # Opzionalmente, recupera le etichette disponibili dall'account
        try:
            email_service = EmailService(
                self.config.email,
                self.config.password,
                self.config.imap_server,
                self.config.imap_port
            )
            context['available_labels'] = email_service.list_labels()
        except Exception as e:
            logger.error(f"Errore nel recupero delle etichette: {str(e)}")
            messages.warning(self.request, f"Impossibile recuperare le etichette: {str(e)}")
        
        return context

class EmailLabelUpdateView(LoginRequiredMixin, UpdateView):
    """
    Aggiorna un'etichetta email esistente.
    """
    model = EmailLabel
    form_class = EmailLabelForm
    template_name = 'email_integration/email_label_form.html'
    
    def get_queryset(self):
        self.config = get_object_or_404(EmailConfig, pk=self.kwargs['config_id'], user=self.request.user)
        return EmailLabel.objects.filter(config=self.config)
    
    def get_success_url(self):
        return reverse_lazy('email_integration:email_label_list', kwargs={'config_id': self.kwargs['config_id']})
    
    def form_valid(self, form):
        messages.success(self.request, 'Etichetta email aggiornata con successo.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = self.config
        context['active_tab'] = 'email_config'
        context['title'] = 'Modifica Etichetta Email'
        return context

class EmailLabelDeleteView(LoginRequiredMixin, DeleteView):
    """
    Elimina un'etichetta email.
    """
    model = EmailLabel
    template_name = 'email_integration/email_label_confirm_delete.html'
    
    def get_queryset(self):
        self.config = get_object_or_404(EmailConfig, pk=self.kwargs['config_id'], user=self.request.user)
        return EmailLabel.objects.filter(config=self.config)
    
    def get_success_url(self):
        return reverse_lazy('email_integration:email_label_list', kwargs={'config_id': self.kwargs['config_id']})
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Etichetta email eliminata con successo.')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = self.config
        context['active_tab'] = 'email_config'
        return context

class EmailImportView(LoginRequiredMixin, FormView):
    """
    Vista per importare manualmente le email da un'etichetta.
    """
    template_name = 'email_integration/email_import_form.html'
    form_class = EmailImportForm
    
    def get_success_url(self):
        return reverse_lazy('email_integration:dashboard')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.label = get_object_or_404(EmailLabel, pk=self.kwargs['label_id'])
        self.config = self.label.config
        
        # Verifica che l'utente abbia accesso a questa configurazione
        if self.config.user != self.request.user:
            raise PermissionError("Non hai i permessi per accedere a questa configurazione")
            
        kwargs['label'] = self.label
        return kwargs
    
    def form_valid(self, form):
        try:
            # Esegui l'importazione
            import_service = EmailImportService(self.label)
            total_emails, created_tasks = import_service.import_emails()
            
            messages.success(
                self.request, 
                f'Importazione completata. {total_emails} email trovate, {created_tasks} nuovi task creati.'
            )
            return super().form_valid(form)
            
        except Exception as e:
            logger.exception(f"Errore nell'importazione delle email: {str(e)}")
            messages.error(self.request, f"Errore nell'importazione delle email: {str(e)}")
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['label'] = self.label
        context['config'] = self.config
        context['active_tab'] = 'email_config'
        return context

class ImportedEmailListView(LoginRequiredMixin, ListView):
    """
    Lista delle email importate per un'etichetta.
    """
    model = ImportedEmail
    template_name = 'email_integration/imported_email_list.html'
    context_object_name = 'emails'
    paginate_by = 20
    
    def get_queryset(self):
        self.label = get_object_or_404(EmailLabel, pk=self.kwargs['label_id'])
        self.config = self.label.config
        
        # Verifica che l'utente abbia accesso a questa configurazione
        if self.config.user != self.request.user:
            raise PermissionError("Non hai i permessi per accedere a questa configurazione")
            
        return ImportedEmail.objects.filter(label=self.label).order_by('-imported_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['label'] = self.label
        context['config'] = self.config
        context['active_tab'] = 'email_config'
        return context

class ImportedEmailDetailView(LoginRequiredMixin, DetailView):
    """
    Dettaglio di un'email importata.
    """
    model = ImportedEmail
    template_name = 'email_integration/imported_email_detail.html'
    context_object_name = 'email'
    
    def get_queryset(self):
        email = get_object_or_404(ImportedEmail, pk=self.kwargs['pk'])
        config = email.label.config
        
        # Verifica che l'utente abbia accesso a questa configurazione
        if config.user != self.request.user:
            raise PermissionError("Non hai i permessi per accedere a questa configurazione")
            
        return ImportedEmail.objects.filter(pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['label'] = self.object.label
        context['config'] = self.object.label.config
        context['active_tab'] = 'email_config'
        return context