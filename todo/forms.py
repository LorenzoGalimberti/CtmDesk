from django import forms
from django.utils.html import format_html
from .models import Task
from core.models import Cliente  # Importa il modello da core

class ClienteChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Visualizza il nome del cliente con i colori definiti nel modello core
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 5px; border-radius: 3px;">{}</span>',
            obj.colore_sfondo, obj.colore_testo, obj.nome
        )

class TaskForm(forms.ModelForm):
    # Utilizza il campo personalizzato per il cliente
    cliente = ClienteChoiceField(
        queryset=Cliente.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Task
        fields = ['title', 'cliente', 'description']
        labels = {
            'title': 'Titolo',
            'cliente': 'Cliente',
            'description': 'Descrizione',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }
