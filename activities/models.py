# activities/models.py
from django.db import models
from core.models import Cliente
import os

def attivita_upload_path(instance, filename):
    """Genera il percorso di upload per i file delle attività"""
    return f'activities/attivita_{instance.attivita.id}/{filename}'

class Categoria(models.Model):
    nome = models.CharField(max_length=255, unique=True, verbose_name="Nome Categoria")
    descrizione = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    colore = models.CharField(max_length=7, default='#6c757d', verbose_name="Colore", 
                              help_text="Colore esadecimale (es. #FF5733)")
    icona = models.CharField(max_length=50, default='bi-folder', verbose_name="Icona Bootstrap",
                             help_text="Nome icona Bootstrap (es. bi-folder, bi-gear)")
    ordinamento = models.PositiveIntegerField(default=0, verbose_name="Ordinamento",
                                              help_text="Ordine di visualizzazione (0 = primo)")
    attiva = models.BooleanField(default=True, verbose_name="Attiva")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorie"
        ordering = ['ordinamento', 'nome']
    
    def __str__(self):
        return self.nome
    
    @property
    def attivita_count(self):
        """Restituisce il numero di attività in questa categoria"""
        return self.attivita.count()
    
    @property
    def attivita_aperte_count(self):
        """Restituisce il numero di attività aperte in questa categoria"""
        return self.attivita.filter(stato='aperta').count()

class Richiedente(models.Model):
    nome = models.CharField(max_length=255)
    cognome = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='richiedenti')
    attivo = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Richiedente"
        verbose_name_plural = "Richiedenti"
        ordering = ['cognome', 'nome']
    
    def __str__(self):
        return f"{self.nome} {self.cognome} ({self.cliente.nome})"
    
    @property
    def nome_completo(self):
        return f"{self.nome} {self.cognome}"
    
    @property 
    def attivita_aperte_count(self):
        """Restituisce il numero di attività aperte per questo richiedente"""
        return self.attivita.filter(stato='aperta').count()
    
    @property
    def attivita_chiuse_count(self):
        """Restituisce il numero di attività chiuse per questo richiedente"""
        return self.attivita.filter(stato='chiusa').count()
    
    @property
    def attivita_totali_count(self):
        """Restituisce il numero totale di attività per questo richiedente"""
        return self.attivita.count()

class Attivita(models.Model):
    STATO_CHOICES = [
        ('aperta', 'Aperta'),
        ('chiusa', 'Chiusa'),
    ]
    
    nome_flusso = models.CharField(max_length=255, verbose_name="Nome Flusso")
    richiedente = models.ForeignKey(Richiedente, on_delete=models.CASCADE, related_name='attivita')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='attivita', 
                                  verbose_name="Categoria")
    stato = models.CharField(max_length=10, choices=STATO_CHOICES, default='aperta')
    
    # Campi aggiuntivi utili
    descrizione = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    data_creazione = models.DateTimeField(auto_now_add=True, verbose_name="Data Creazione")
    data_chiusura = models.DateTimeField(blank=True, null=True, verbose_name="Data Chiusura")
    note = models.TextField(blank=True, null=True, verbose_name="Note")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Attività"
        verbose_name_plural = "Attività"
        ordering = ['-data_creazione']
    
    def __str__(self):
        return f"{self.nome_flusso} - {self.richiedente.nome_completo} ({self.get_stato_display()})"
    
    @property
    def cliente(self):
        """Restituisce il cliente associato al richiedente"""
        return self.richiedente.cliente
    
    def chiudi_attivita(self):
        """Metodo per chiudere l'attività"""
        from django.utils import timezone
        self.stato = 'chiusa'
        self.data_chiusura = timezone.now()
        self.save()
    
    def riapri_attivita(self):
        """Metodo per riaprire l'attività"""
        self.stato = 'aperta'
        self.data_chiusura = None
        self.save()
    
    @property
    def is_aperta(self):
        return self.stato == 'aperta'
    
    @property
    def is_chiusa(self):
        return self.stato == 'chiusa'
    
    @property
    def allegati_count(self):
        """Restituisce il numero di allegati dell'attività"""
        return self.allegati.count()
    
    # METODI PER STATISTICHE TASK
    @property
    def task_totali_count(self):
        """Restituisce il numero totale di task collegati"""
        return self.tasks.count()
    
    @property
    def task_completati_count(self):
        """Restituisce il numero di task completati"""
        return self.tasks.filter(completed=True).count()
    
    @property
    def task_in_corso_count(self):
        """Restituisce il numero di task in corso (non completati e non archiviati)"""
        return self.tasks.filter(completed=False, archiviato=False).count()
    
    @property
    def task_archiviati_count(self):
        """Restituisce il numero di task archiviati"""
        return self.tasks.filter(archiviato=True).count()
    
    @property
    def has_tasks(self):
        """Verifica se l'attività ha task collegati"""
        return self.tasks.exists()
    
    @property
    def all_tasks_completed(self):
        """Verifica se tutti i task sono completati"""
        if not self.has_tasks:
            return False
        return not self.tasks.filter(completed=False, archiviato=False).exists()
    
    @property
    def task_completion_percentage(self):
        """Calcola la percentuale di completamento dei task"""
        if not self.has_tasks:
            return 0
        total = self.task_totali_count
        completed = self.task_completati_count
        return round((completed / total) * 100) if total > 0 else 0

class AllegatoAttivita(models.Model):
    """Modello per gestire i file allegati alle attività"""
    
    attivita = models.ForeignKey(Attivita, on_delete=models.CASCADE, related_name='allegati')
    file = models.FileField(upload_to='allegati_attivita/%Y/%m/')
    nome_originale = models.CharField(max_length=255, blank=True)
    descrizione = models.CharField(max_length=500, blank=True, null=True)
    dimensione = models.PositiveIntegerField(default=0)  # in bytes
    tipo_mime = models.CharField(max_length=100, blank=True)
    caricato_il = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-caricato_il']
        verbose_name = 'Allegato Attività'
        verbose_name_plural = 'Allegati Attività'
    
    def save(self, *args, **kwargs):
        """Override del save per salvare metadati del file"""
        if self.file:
            self.nome_originale = self.file.name
            self.dimensione = self.file.size
            
            # Determina il tipo MIME
            file_extension = os.path.splitext(self.file.name)[1].lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
                '.zip': 'application/zip',
                '.rar': 'application/x-rar-compressed',
                '.7z': 'application/x-7z-compressed',
            }
            self.tipo_mime = mime_types.get(file_extension, 'application/octet-stream')
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override del delete per rimuovere anche il file fisico"""
        from django.core.files.storage import default_storage
        if self.file and default_storage.exists(self.file.name):
            default_storage.delete(self.file.name)
        super().delete(*args, **kwargs)
    
    @property
    def dimensione_formattata(self):
        """Restituisce la dimensione del file in formato leggibile"""
        if self.dimensione < 1024:
            return f"{self.dimensione} B"
        elif self.dimensione < 1024 * 1024:
            return f"{self.dimensione / 1024:.1f} KB"
        elif self.dimensione < 1024 * 1024 * 1024:
            return f"{self.dimensione / (1024 * 1024):.1f} MB"
        else:
            return f"{self.dimensione / (1024 * 1024 * 1024):.1f} GB"
    
    @property
    def is_image(self):
        """Verifica se il file è un'immagine"""
        return self.tipo_mime.startswith('image/')
    
    @property
    def is_pdf(self):
        """Verifica se il file è un PDF"""
        return self.tipo_mime == 'application/pdf'
    
    @property
    def is_office_document(self):
        """Verifica se il file è un documento Office"""
        office_types = [
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ]
        return self.tipo_mime in office_types
    
    @property
    def is_text(self):
        """Verifica se il file è di testo"""
        return self.tipo_mime.startswith('text/')
    
    @property
    def icona_file(self):
        """Restituisce l'icona Bootstrap appropriata per il tipo di file"""
        if self.is_image:
            return 'bi-file-earmark-image'
        elif self.is_pdf:
            return 'bi-file-earmark-pdf'
        elif self.tipo_mime == 'application/msword' or 'wordprocessing' in self.tipo_mime:
            return 'bi-file-earmark-word'
        elif 'spreadsheet' in self.tipo_mime or 'excel' in self.tipo_mime:
            return 'bi-file-earmark-excel'
        elif 'presentation' in self.tipo_mime or 'powerpoint' in self.tipo_mime:
            return 'bi-file-earmark-ppt'
        elif self.is_text:
            return 'bi-file-earmark-text'
        elif 'zip' in self.tipo_mime or 'compressed' in self.tipo_mime:
            return 'bi-file-earmark-zip'
        else:
            return 'bi-file-earmark'
    
    @property
    def can_preview(self):
        """Verifica se il file può essere visualizzato in anteprima"""
        return True
    
    def __str__(self):
        return f"{self.nome_originale} - {self.attivita.nome_flusso}"