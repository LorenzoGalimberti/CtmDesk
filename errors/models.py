from django.db import models

from core.models import Cliente


class Errore(models.Model):
    LIVELLO_CHOICES = [
        ('basso', 'Basso'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    data = models.DateField()
    ambiente = models.CharField(max_length=100)
    note = models.TextField(blank=True)
    livello = models.CharField(max_length=10, choices=LIVELLO_CHOICES)
    occorrenze = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cliente.nome} - {self.livello} ({self.data})"
