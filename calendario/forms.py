# calendario/forms.py
from django import forms
from .models import Evento
from core.models import Cliente

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            'titolo', 
            'descrizione', 
            'data_inizio', 
            'data_fine',
            'cliente'
        ]
        widgets = {
            'titolo': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': "Titolo dell'evento"
            }),
            'descrizione': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': "Descrizione dell'evento", 
                'rows': 4
            }),
            'data_inizio': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
            'data_fine': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].required = False
        self.fields['cliente'].empty_label = "Seleziona un cliente (opzionale)"