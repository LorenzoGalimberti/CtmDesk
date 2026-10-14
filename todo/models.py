# todo/models.py
from django.conf import settings
from django.db import models
from datetime import datetime
from core.models import Cliente

class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ('manual', 'Manuale'),
        ('activity', 'Da Attività'),
    ]
    
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        verbose_name='Proprietario',
    )
    completed = models.BooleanField(default=False)
    archiviato = models.BooleanField(default=False)
    data_creazione = models.DateField(null=True, blank=True)
    data_archiviazione = models.DateField(null=True, blank=True)
    order = models.IntegerField(default=0)
    
    # Campo per distinguere il tipo di task
    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPE_CHOICES,
        default='manual',
        verbose_name='Tipo Task'
    )
    
    # Collegamento all'attività (se creato da un'attività)
    attivita = models.ForeignKey(
        'activities.Attivita',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tasks'
    )
    
    # Collegamento al Cliente
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )

    description = models.TextField(blank=True, null=True)

    def __str__(self):
        tipo_icon = "📋" if self.task_type == 'activity' else "📝"
        return f"{tipo_icon} {self.title}"

    def archive(self):
        self.archiviato = True
        self.data_archiviazione = datetime.now().date()
        self.save()

    def is_due(self):
        return bool(self.data_creazione) and self.data_creazione < datetime.now().date()
    
    @property
    def icon_class(self):
        """Restituisce la classe dell'icona Bootstrap Icons"""
        if self.task_type == 'activity':
            return 'bi-clipboard-check'  # Icona per task da attività
        return 'bi-check-square'  # Icona standard per task manuali
    
    @property
    def badge_color(self):
        """Restituisce il colore del badge per il tipo"""
        if self.task_type == 'activity':
            return 'bg-info'  # Blu per task da attività
        return 'bg-secondary'  # Grigio per task manuali

    class Meta:
        ordering = ['data_creazione', 'order']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'