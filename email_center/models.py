# email_integration/models.py
from django.db import models
from django.conf import settings

class EmailConfig(models.Model):
    """
    Configurazione per l'accesso all'email.
    Nota: In un ambiente di produzione, dovresti usare una soluzione più sicura
    per memorizzare le password, come django-encrypted-fields o servizi come AWS Secrets Manager.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                            related_name='email_configs', null=True, blank=True)
    email = models.EmailField('Indirizzo Email')
    # In produzione, usa una soluzione di crittografia come django-encrypted-fields
    password = models.CharField('Password', max_length=255) 
    imap_server = models.CharField('Server IMAP', max_length=100, default='imap.gmail.com')
    imap_port = models.IntegerField('Porta IMAP', default=993)
    active = models.BooleanField('Attivo', default=True)
    created_at = models.DateTimeField('Data creazione', auto_now_add=True)
    updated_at = models.DateTimeField('Data aggiornamento', auto_now=True)
    
    class Meta:
        verbose_name = 'Configurazione Email'
        verbose_name_plural = 'Configurazioni Email'
    
    def __str__(self):
        return self.email

class EmailLabel(models.Model):
    """
    Etichette email da monitorare per l'importazione automatica.
    """
    name = models.CharField('Nome etichetta', max_length=100)
    config = models.ForeignKey(EmailConfig, on_delete=models.CASCADE, related_name='labels')
    import_as_priority = models.CharField('Priorità predefinita', max_length=50, 
                                        default='MEDIUM',
                                        choices=[
                                            ('LOW', 'Bassa'),
                                            ('MEDIUM', 'Media'),
                                            ('HIGH', 'Alta'),
                                            ('URGENT', 'Urgente')
                                        ])
    max_emails = models.IntegerField('Numero max email da importare', default=20)
    active = models.BooleanField('Attiva', default=True)
    last_import = models.DateTimeField('Ultima importazione', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Etichetta Email'
        verbose_name_plural = 'Etichette Email'
        unique_together = ('name', 'config')
    
    def __str__(self):
        return f"{self.name} ({self.config.email})"

class ImportedEmail(models.Model):
    """
    Registro delle email importate, per evitare duplicati.
    """
    message_id = models.CharField('ID Messaggio', max_length=255, unique=True)
    subject = models.CharField('Oggetto', max_length=255, blank=True)
    sender = models.CharField('Mittente', max_length=255)
    received_at = models.DateTimeField('Data ricezione')
    label = models.ForeignKey(EmailLabel, on_delete=models.CASCADE, related_name='imported_emails')
    task = models.ForeignKey('todo.Task', on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='source_email')
    imported_at = models.DateTimeField('Data importazione', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Email Importata'
        verbose_name_plural = 'Email Importate'
        ordering = ['-received_at']
    
    def __str__(self):
        return self.subject or "Email senza oggetto"