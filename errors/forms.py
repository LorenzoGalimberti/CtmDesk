from django import forms
from .models import Errore

class ErroreForm(forms.ModelForm):
    class Meta:
        model = Errore
        # Elenchiamo i campi in modo esplicito per avere più controllo
        fields = [
            'cliente',
            'data',
            'ambiente',
            'note',
            'livello',
            'occorrenze'
        ]

        # Label personalizzate (facoltative) per ciascun campo
        labels = {
            'cliente': 'Cliente',
            'data': 'Data Errore',
            'ambiente': 'Ambiente',
            'note': 'Note/Dettagli',
            'livello': 'Livello di Gravità',
            'occorrenze': 'Numero di Occorrenze'
        }

        # Tooltip o breve testo esplicativo (facoltativo)
        help_texts = {
            'note': 'Aggiungi qui eventuali informazioni aggiuntive',
            'occorrenze': 'Quante volte si è verificato questo errore?'
        }

        # Widget personalizzati per sfruttare le classi Bootstrap
        widgets = {
            'cliente': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nome del cliente'
                }
            ),
            'data': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'ambiente': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Es. Produzione / Test / Sviluppo'
                }
            ),
            'note': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Descrizione dettagliata dell’errore'
                }
            ),
            'livello': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'occorrenze': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 1
                }
            ),
        }
