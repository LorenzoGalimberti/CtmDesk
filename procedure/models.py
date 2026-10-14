from django.db import models

class Ambiente(models.Model):
    nome = models.CharField(max_length=255)
    
    def __str__(self):
        return self.nome

class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    
    def __str__(self):
        return self.nome

class Tipologia(models.Model):
    nome = models.CharField(max_length=255)
    
    def __str__(self):
        return self.nome

class Procedura(models.Model):
    nome = models.CharField(max_length=255)
    ambiente = models.ForeignKey(Ambiente, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    tipologia = models.ForeignKey(Tipologia, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome

from django.db import models

class Step(models.Model):
    procedura = models.ForeignKey(Procedura, on_delete=models.CASCADE, related_name='steps')
    titolo = models.CharField(max_length=255)
    corpo = models.TextField()
    immagini = models.ImageField(upload_to='steps_images/', blank=True, null=True)
    ordine = models.PositiveIntegerField(default=0)  # Valore predefinito

    class Meta:
        ordering = ['ordine']  # Ordina gli step per default

    def __str__(self):
        return f"{self.procedura.nome} - {self.titolo}"
