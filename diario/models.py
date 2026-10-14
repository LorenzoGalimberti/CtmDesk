from django.conf import settings
from django.db import models
from core.models import Cliente  # Importa il modello Cliente dall'app core


class Tag(models.Model):
    nome = models.CharField(max_length=100, unique=True)  # Nome del tag, unico per evitare duplicati
    colore_sfondo = models.CharField(max_length=7, default='#FFFFFF')  # Colore di sfondo (esadecimale)
    colore_testo = models.CharField(max_length=7, default='#000000')  # Colore del testo (esadecimale)

    def __str__(self):
        return self.nome


class Diario(models.Model):
    titolo = models.CharField(max_length=200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        verbose_name='Proprietario',
    )
    contenuto = models.TextField()
    data_creazione = models.DateTimeField()
    tags = models.ManyToManyField(Tag, related_name='diari', blank=True)  # Manteniamo per retrocompatibilità
    clienti = models.ManyToManyField(Cliente, related_name='diari', blank=True)  # Aggiungiamo relazione con i clienti

    def __str__(self):
        return self.titolo