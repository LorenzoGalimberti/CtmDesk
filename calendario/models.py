# calendario/models.py
from django.conf import settings
from django.db import models
from core.models import Cliente  # Importa Cliente dal core

class Evento(models.Model):
    titolo = models.CharField(max_length=200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        verbose_name='Proprietario',
    )
    descrizione = models.TextField(blank=True, null=True)
    data_inizio = models.DateTimeField()
    data_fine = models.DateTimeField()
    archived = models.BooleanField(default=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.titolo

    def as_dict(self):
        return {
            'id': self.id,
            'title': self.titolo,
            'description': self.descrizione,
            'start': self.data_inizio.isoformat(),
            'end': self.data_fine.isoformat(),
            # Se l'evento ha un cliente, usiamo i suoi colori
            'backgroundColor': self.cliente.colore_sfondo if self.cliente else '#cccccc',
            'textColor': self.cliente.colore_testo if self.cliente else '#000000',
            'clienteNome': self.cliente.nome if self.cliente else 'Nessun cliente',
        }