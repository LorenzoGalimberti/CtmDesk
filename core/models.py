from django.db import models

# Create your models here.
from django.db import models

class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    colore_sfondo = models.CharField(max_length=7)  # Esempio: "#ffffff"
    colore_testo = models.CharField(max_length=7)    # Esempio: "#000000"
    
    def __str__(self):
        return self.nome
