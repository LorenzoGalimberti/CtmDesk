import json
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from activities.models import Attivita, Categoria, Richiedente
from core.models import Cliente
from errors.models import Errore
from procedura.models import Procedura, Step
from todo.models import Task


class BaseTestCase(TestCase):
    """Crea un utente, fa il login e prepara un cliente di prova."""

    def setUp(self):
        self.user = get_user_model().objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        self.cliente = Cliente.objects.create(
            nome='ACME', colore_sfondo='#ffffff', colore_testo='#000000'
        )


class LoginTests(TestCase):
    def test_anonimo_viene_mandato_al_login(self):
        risposta = self.client.get(reverse('home'))
        self.assertEqual(risposta.status_code, 302)
        self.assertTrue(risposta.url.startswith(reverse('login')))

    def test_pagina_di_login_accessibile(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)


class PagineTests(BaseTestCase):
    def test_pagine_principali_si_aprono(self):
        nomi = [
            'home', 'errore_list', 'errore_create', 'calendario', 'lista_eventi',
            'procedura-list', 'procedura-create', 'step-list',
            'activities-dashboard', 'attivita-list', 'attivita-create',
            'categoria-list', 'categoria-create',
            'richiedente-list', 'richiedente-create',
            'todo:task_list', 'todo:all_task',
            'diario:diario_list', 'tools:index', 'tools:impatti_fermi',
        ]
        for nome in nomi:
            with self.subTest(pagina=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)


class ClienteUnicoTests(BaseTestCase):
    def test_errore_e_procedura_usano_il_cliente_di_core(self):
        errore = Errore.objects.create(
            cliente=self.cliente, data=date.today(), ambiente='Test',
            livello='basso', occorrenze=1,
        )
        procedura = Procedura.objects.create(nome='Proc', cliente=self.cliente)
        self.assertEqual(errore.cliente, self.cliente)
        self.assertEqual(procedura.cliente, self.cliente)

    def test_home_conta_i_clienti(self):
        risposta = self.client.get(reverse('home'))
        self.assertEqual(risposta.context['total_clients'], 1)

    def test_form_errori_ha_menu_a_tendina_dei_clienti(self):
        risposta = self.client.get(reverse('errore_create'))
        self.assertContains(risposta, '<select name="cliente"')


class AttivitaTaskTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        richiedente = Richiedente.objects.create(
            nome='Mario', cognome='Rossi', cliente=self.cliente
        )
        categoria = Categoria.objects.create(nome='Test')
        self.attivita = Attivita.objects.create(
            nome_flusso='Flusso', richiedente=richiedente, categoria=categoria
        )
        self.task = Task.objects.create(
            title='Lavorare', attivita=self.attivita,
            task_type='activity', data_creazione=date.today(),
        )

    def test_chiudere_attivita_completa_i_task(self):
        self.client.get(reverse('attivita-chiudi', args=[self.attivita.pk]))
        self.attivita.refresh_from_db()
        self.task.refresh_from_db()
        self.assertEqual(self.attivita.stato, 'chiusa')
        self.assertTrue(self.task.completed)

    def test_riaprire_attivita_riapre_i_task(self):
        self.client.get(reverse('attivita-chiudi', args=[self.attivita.pk]))
        self.client.get(reverse('attivita-riapri', args=[self.attivita.pk]))
        self.attivita.refresh_from_db()
        self.task.refresh_from_db()
        self.assertEqual(self.attivita.stato, 'aperta')
        self.assertFalse(self.task.completed)

    def test_completare_ultimo_task_chiude_attivita(self):
        risposta = self.client.post(reverse('todo:complete_task', args=[self.task.pk]))
        self.assertTrue(risposta.json().get('activity_closed'))
        self.attivita.refresh_from_db()
        self.assertEqual(self.attivita.stato, 'chiusa')


class CategorieTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.categoria = Categoria.objects.create(nome='Da provare')

    def test_pagina_di_dettaglio(self):
        risposta = self.client.get(reverse('categoria-detail', args=[self.categoria.pk]))
        self.assertEqual(risposta.status_code, 200)

    def test_pagina_di_conferma_eliminazione(self):
        risposta = self.client.get(reverse('categoria-delete', args=[self.categoria.pk]))
        self.assertEqual(risposta.status_code, 200)

    def test_eliminazione_mostra_il_messaggio(self):
        risposta = self.client.post(
            reverse('categoria-delete', args=[self.categoria.pk]), follow=True
        )
        self.assertFalse(Categoria.objects.filter(pk=self.categoria.pk).exists())
        testi = [str(m) for m in risposta.context['messages']]
        self.assertIn('Categoria eliminata con successo!', testi)


class StepTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.procedura = Procedura.objects.create(nome='Proc', cliente=self.cliente)
        self.s1 = Step.objects.create(procedura=self.procedura, titolo='Uno', corpo='x')
        self.s2 = Step.objects.create(procedura=self.procedura, titolo='Due', corpo='x')
        self.s3 = Step.objects.create(procedura=self.procedura, titolo='Tre', corpo='x')

    def _ordine_salvato(self):
        return list(
            Step.objects.filter(procedura=self.procedura)
            .order_by('ordine').values_list('pk', flat=True)
        )

    def _riordina(self, ids):
        return self.client.post(
            reverse('update-step-order'),
            data=json.dumps({'step_order': ids}),
            content_type='application/json',
        )

    def test_riordino_step(self):
        nuovo = [self.s3.pk, self.s1.pk, self.s2.pk]
        self.assertEqual(self._riordina(nuovo).status_code, 200)
        self.assertEqual(self._ordine_salvato(), nuovo)

    def test_riordino_con_dati_non_validi(self):
        risposta = self.client.post(
            reverse('update-step-order'), data='non json', content_type='application/json'
        )
        self.assertEqual(risposta.status_code, 400)

    def test_navigazione_tra_step(self):
        risposta = self.client.get(reverse('step-detail', args=[self.s2.pk]))
        self.assertEqual(risposta.context['previous_step'], self.s1)
        self.assertEqual(risposta.context['next_step'], self.s3)
        self.assertEqual(risposta.context['current_position'], 2)
        self.assertEqual(risposta.context['total_steps'], 3)

    def test_aprire_il_primo_step_non_cambia_l_ordine(self):
        nuovo = [self.s3.pk, self.s1.pk, self.s2.pk]
        self._riordina(nuovo)
        self.client.get(reverse('step-detail', args=[self.s3.pk]))
        self.assertEqual(self._ordine_salvato(), nuovo)
