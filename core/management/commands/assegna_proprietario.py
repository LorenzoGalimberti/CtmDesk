from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from activities.models import Attivita
from calendario.models import Evento
from diario.models import Diario
from errors.models import Errore
from procedura.models import Procedura
from todo.models import Task


class Command(BaseCommand):
    help = "Assegna a un utente tutti i dati personali che non hanno ancora un proprietario."

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            utente = User.objects.get(username=options['username'])
        except User.DoesNotExist:
            raise CommandError(f"Utente '{options['username']}' non trovato")

        for modello in (Attivita, Task, Evento, Errore, Diario, Procedura):
            n = modello.objects.filter(owner__isnull=True).update(owner=utente)
            self.stdout.write(f"{modello.__name__}: {n} assegnati a {utente.username}")
