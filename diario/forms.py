from django import forms
from django.contrib.auth import get_user_model
from .models import Diario
from core.models import Cliente  # Importa il modello Cliente dall'app core
from django_summernote.widgets import SummernoteWidget

class DiarioForm(forms.ModelForm):
    clienti = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.all(),
        required=False,  # Campo opzionale
        widget=forms.CheckboxSelectMultiple,  # Mostra come elenco di checkbox
    )

    condiviso_con = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Condividi con',
    )

    class Meta:
        model = Diario
        fields = ['titolo', 'contenuto', 'clienti', 'condiviso_con']
        
        widgets = {
            'contenuto': SummernoteWidget(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super(DiarioForm, self).__init__(*args, **kwargs)
        utenti = get_user_model().objects.filter(is_active=True).order_by('username')
        if user is not None:
            utenti = utenti.exclude(pk=user.pk)
        self.fields['condiviso_con'].queryset = utenti
        self.fields['condiviso_con'].label_from_instance = lambda u: u.get_full_name() or u.get_username()
        self.fields['condiviso_con'].widget.attrs.update({'class': 'form-check-input'})
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