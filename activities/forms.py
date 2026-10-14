from django import forms
from .models import Attivita, Richiedente, Categoria, AllegatoAttivita
from core.models import Cliente

class AttivitaForm(forms.ModelForm):
    class Meta:
        model = Attivita
        fields = ['nome_flusso', 'richiedente', 'categoria', 'stato', 'descrizione', 'note']
        widgets = {
            'nome_flusso': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inserisci il nome del flusso'
            }),
            'richiedente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'stato': forms.Select(attrs={
                'class': 'form-control'
            }),
            'descrizione': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrizione dettagliata dell\'attività'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Note aggiuntive'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordina i richiedenti per cliente e nome
        self.fields['richiedente'].queryset = Richiedente.objects.select_related('cliente').filter(attivo=True).order_by('cliente__nome', 'cognome', 'nome')
        
        # Ordina le categorie per ordinamento e nome
        self.fields['categoria'].queryset = Categoria.objects.filter(attiva=True).order_by('ordinamento', 'nome')
        
        # Personalizza le etichette nel dropdown dei richiedenti
        self.fields['richiedente'].label_from_instance = lambda obj: f"{obj.nome_completo} ({obj.cliente.nome})"
        
        # Personalizza le etichette nel dropdown delle categorie
        self.fields['categoria'].label_from_instance = lambda obj: f"{obj.nome}"

class AllegatoAttivitaForm(forms.ModelForm):
    class Meta:
        model = AllegatoAttivita
        fields = ['file', 'descrizione']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.zip,.rar,.txt,.csv'
            }),
            'descrizione': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrizione del file (opzionale)',
                'maxlength': '500'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Controlla la dimensione del file (max 50MB)
            if file.size > 50 * 1024 * 1024:  # 50MB
                raise forms.ValidationError('Il file è troppo grande. Dimensione massima: 50MB')
            
            # Controlla l'estensione del file
            import os
            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
                '.zip', '.rar', '.7z',
                '.txt', '.csv', '.xml', '.json'
            ]
            
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    f'Tipo di file non supportato. Estensioni consentite: {", ".join(allowed_extensions)}'
                )
        
        return file

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descrizione', 'colore', 'icona', 'ordinamento', 'attiva']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome della categoria'
            }),
            'descrizione': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrizione della categoria'
            }),
            'colore': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#6c757d'
            }),
            'icona': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'bi-folder (icona Bootstrap)'
            }),
            'ordinamento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'attiva': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        if nome:
            # Verifica che il nome non sia già utilizzato da un'altra categoria
            existing = Categoria.objects.filter(nome__iexact=nome)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError('Una categoria con questo nome esiste già.')
        return nome

class RichiedenteForm(forms.ModelForm):
    class Meta:
        model = Richiedente
        fields = ['nome', 'cognome', 'email', 'telefono', 'cliente', 'attivo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome'
            }),
            'cognome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cognome'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@esempio.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+39 123 456 7890'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'attivo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordina i clienti per nome
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('nome')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:  # Solo se l'email è fornita
            # Verifica che l'email non sia già utilizzata da un altro richiedente
            existing = Richiedente.objects.filter(email=email)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError('Questa email è già utilizzata da un altro richiedente.')
        return email

class AttivitaFilterForm(forms.Form):
    """Form per filtrare le attività nella lista"""
    STATO_CHOICES = [
        ('', 'Tutti gli stati'),
        ('aperta', 'Aperta'),
        ('chiusa', 'Chiusa'),
    ]
    
    stato = forms.ChoiceField(
        choices=STATO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        required=False,
        empty_label="Tutti i clienti",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(attiva=True),
        required=False,
        empty_label="Tutte le categorie",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cerca per nome flusso, richiedente o descrizione...'
        })
    )

class RichiedenteFilterForm(forms.Form):
    """Form per filtrare i richiedenti nella lista"""
    ATTIVO_CHOICES = [
        ('', 'Tutti'),
        ('true', 'Solo attivi'),
        ('false', 'Solo non attivi'),
    ]
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        required=False,
        empty_label="Tutti i clienti",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    attivo = forms.ChoiceField(
        choices=ATTIVO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cerca per nome, cognome o email...'
        })
    )