from django import forms
from .models import Diario
from core.models import Cliente  # Importa il modello Cliente dall'app core
from django_summernote.widgets import SummernoteWidget

class DiarioForm(forms.ModelForm):
    clienti = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.all(),
        required=False,  # Campo opzionale
        widget=forms.CheckboxSelectMultiple,  # Mostra come elenco di checkbox
    )

    class Meta:
        model = Diario
        fields = ['titolo', 'contenuto', 'clienti']  # Rimosso 'tags' dalla lista
        
        widgets = {
            'contenuto': SummernoteWidget(),
        }

    def __init__(self, *args, **kwargs):
        super(DiarioForm, self).__init__(*args, **kwargs)
        self.fields['titolo'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Inserisci il titolo della nota'
        })
        self.fields['contenuto'].widget.attrs.update({
            'class': 'form-control summernote',
            'placeholder': 'Scrivi il contenuto della nota...'
        })
        self.fields['clienti'].widget.attrs.update({
            'class': 'form-check-input',  # Classi per i checkbox
        })