from django.db import models
from django.db.models import Max

from core.models import Cliente


class Ambiente(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


class Tipologia(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


class Procedura(models.Model):
    nome = models.CharField(max_length=255)
    ambiente = models.ForeignKey(Ambiente, blank=True, null=True, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    tipologia = models.ForeignKey(Tipologia, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome


class Step(models.Model):
    procedura = models.ForeignKey(Procedura, on_delete=models.CASCADE, related_name='steps')
    titolo = models.CharField(max_length=255)
    corpo = models.TextField()
    immagini = models.ImageField(upload_to='steps_images/', blank=True, null=True)
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine']

    def save(self, *args, **kwargs):
        if self.pk is None:  # Se è un nuovo oggetto
            # Recupera il valore massimo attuale dell'ordine per la stessa procedura
            last_order = Step.objects.filter(procedura=self.procedura).aggregate(Max('ordine'))['ordine__max']
            self.ordine = 0 if last_order is None else last_order + 1
        super().save(*args, **kwargs)
