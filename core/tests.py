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
            nome_flusso='Flusso', richiedente=richiedente, categoria=categoria,
            owner=self.user,
        )
        self.task = Task.objects.create(
            title='Lavorare', attivita=self.attivita,
            task_type='activity', data_creazione=date.today(), owner=self.user,
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
        self.procedura = Procedura.objects.create(nome='Proc', cliente=self.cliente, owner=self.user)
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


class ProprietarioTests(BaseTestCase):
    """Quello che crei da utente loggato ne diventa il proprietario."""

    def test_attivita_e_task_automatico(self):
        richiedente = Richiedente.objects.create(
            nome='Mario', cognome='Rossi', cliente=self.cliente
        )
        categoria = Categoria.objects.create(nome='Test')
        self.client.post(reverse('attivita-create'), {
            'nome_flusso': 'Flusso nuovo', 'richiedente': richiedente.pk,
            'categoria': categoria.pk, 'stato': 'aperta',
            'descrizione': '', 'note': '',
        })
        attivita = Attivita.objects.get(nome_flusso='Flusso nuovo')
        self.assertEqual(attivita.owner, self.user)
        self.assertEqual(Task.objects.get(attivita=attivita).owner, self.user)

    def test_task_manuale(self):
        self.client.post(reverse('todo:add_task'), {
            'title': 'Prova', 'cliente': self.cliente.pk, 'description': 'x',
        })
        self.assertEqual(Task.objects.get(title='Prova').owner, self.user)

    def test_procedura(self):
        self.client.post(reverse('procedura-create'), {
            'nome': 'Nuova proc', 'cliente': self.cliente.pk,
        })
        self.assertEqual(Procedura.objects.get(nome='Nuova proc').owner, self.user)

    def test_diario(self):
        from diario.models import Diario
        self.client.post(
            reverse('diario:nuovo_diario', args=[2026, 1, 15]),
            {'titolo': 'Nota', 'contenuto': 'testo'},
        )
        self.assertEqual(Diario.objects.get(titolo='Nota').owner, self.user)


class IsolamentoAttivitaTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        altro = get_user_model().objects.create_user('altro', password='x')
        richiedente = Richiedente.objects.create(
            nome='Mario', cognome='Rossi', cliente=self.cliente
        )
        categoria = Categoria.objects.create(nome='Test')
        self.mia = Attivita.objects.create(
            nome_flusso='Mia', richiedente=richiedente, categoria=categoria, owner=self.user
        )
        self.altrui = Attivita.objects.create(
            nome_flusso='Altrui', richiedente=richiedente, categoria=categoria, owner=altro
        )

    def test_la_lista_mostra_solo_le_mie(self):
        risposta = self.client.get(reverse('attivita-list'))
        nomi = [a.nome_flusso for a in risposta.context['attivita']]
        self.assertEqual(nomi, ['Mia'])

    def test_non_posso_aprire_modificare_o_eliminare_quelle_altrui(self):
        for nome in ['attivita-detail', 'attivita-update', 'attivita-delete']:
            with self.subTest(vista=nome):
                url = reverse(nome, args=[self.altrui.pk])
                self.assertEqual(self.client.get(url).status_code, 404)
        self.client.post(reverse('attivita-delete', args=[self.altrui.pk]))
        self.assertTrue(Attivita.objects.filter(pk=self.altrui.pk).exists())

    def test_non_posso_chiudere_quelle_altrui(self):
        risposta = self.client.get(reverse('attivita-chiudi', args=[self.altrui.pk]))
        self.assertEqual(risposta.status_code, 404)
        self.altrui.refresh_from_db()
        self.assertEqual(self.altrui.stato, 'aperta')

    def test_la_dashboard_conta_solo_le_mie(self):
        risposta = self.client.get(reverse('activities-dashboard'))
        self.assertEqual(risposta.context['totale_attivita'], 1)

    def test_le_mie_si_aprono(self):
        risposta = self.client.get(reverse('attivita-detail', args=[self.mia.pk]))
        self.assertEqual(risposta.status_code, 200)


class IsolamentoTodoEventiTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        from django.utils import timezone
        from calendario.models import Evento
        self.altro = get_user_model().objects.create_user('altro', password='x')
        oggi = date.today()
        self.mio_task = Task.objects.create(title='Mio', data_creazione=oggi, owner=self.user)
        self.altrui_task = Task.objects.create(title='Altrui', data_creazione=oggi, owner=self.altro)
        adesso = timezone.now()
        self.mio_evento = Evento.objects.create(
            titolo='Mio evento', data_inizio=adesso, data_fine=adesso, owner=self.user)
        self.altrui_evento = Evento.objects.create(
            titolo='Evento altrui', data_inizio=adesso, data_fine=adesso, owner=self.altro)

    def test_liste_task_solo_miei(self):
        for nome in ['todo:task_list', 'todo:all_task']:
            with self.subTest(pagina=nome):
                risposta = self.client.get(reverse(nome))
                titoli = [t.title for t in risposta.context['tasks']]
                self.assertEqual(titoli, ['Mio'])

    def test_azioni_su_task_altrui_danno_404(self):
        pk = self.altrui_task.pk
        self.assertEqual(self.client.post(reverse('todo:complete_task', args=[pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('todo:archive_task', args=[pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('todo:delete_task', args=[pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('todo:edit_task', args=[pk])).status_code, 404)
        self.altrui_task.refresh_from_db()
        self.assertFalse(self.altrui_task.completed)
        self.assertFalse(self.altrui_task.archiviato)

    def test_calendario_json_solo_miei(self):
        risposta = self.client.get(reverse('eventi_json'))
        self.assertEqual([e['title'] for e in risposta.json()], ['Mio evento'])

    def test_lista_eventi_solo_miei(self):
        risposta = self.client.get(reverse('lista_eventi'))
        self.assertEqual([e.titolo for e in risposta.context['eventi']], ['Mio evento'])

    def test_azioni_su_evento_altrui_danno_404(self):
        from calendario.models import Evento
        pk = self.altrui_evento.pk
        self.assertEqual(self.client.get(reverse('evento_dettaglio', args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('elimina_evento', args=[pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('archivia_evento', args=[pk])).status_code, 404)
        self.altrui_evento.refresh_from_db()
        self.assertFalse(self.altrui_evento.archived)
        self.assertTrue(Evento.objects.filter(pk=pk).exists())

    def test_il_mio_evento_si_apre(self):
        risposta = self.client.get(reverse('evento_dettaglio', args=[self.mio_evento.pk]))
        self.assertEqual(risposta.status_code, 200)


class IsolamentoErroriHomeTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.altro = get_user_model().objects.create_user('altro', password='x')
        dati = dict(cliente=self.cliente, data=date.today(), ambiente='Test',
                    livello='basso', occorrenze=1)
        self.mio = Errore.objects.create(owner=self.user, **dati)
        self.altrui = Errore.objects.create(owner=self.altro, **dati)

    def test_lista_errori_solo_miei(self):
        risposta = self.client.get(reverse('errore_list'))
        self.assertEqual(list(risposta.context['errori']), [self.mio])

    def test_errore_altrui_danno_404(self):
        pk = self.altrui.pk
        for nome in ['errore_detail', 'errore_update', 'errore_delete']:
            with self.subTest(vista=nome):
                self.assertEqual(self.client.get(reverse(nome, args=[pk])).status_code, 404)
        self.client.post(reverse('errore_delete', args=[pk]))
        self.assertTrue(Errore.objects.filter(pk=pk).exists())

    def test_il_mio_errore_si_apre(self):
        self.assertEqual(
            self.client.get(reverse('errore_detail', args=[self.mio.pk])).status_code, 200)

    def test_home_e_ricerca_solo_miei_eventi(self):
        from django.utils import timezone
        from calendario.models import Evento
        adesso = timezone.now()
        for titolo, utente in (('Evento mio', self.user), ('Evento altrui', self.altro)):
            Evento.objects.create(titolo=titolo, data_inizio=adesso, data_fine=adesso,
                                  cliente=self.cliente, owner=utente)
        home = self.client.get(reverse('home'))
        self.assertEqual([e.titolo for e in home.context['eventi_oggi']], ['Evento mio'])
        ricerca = self.client.get(reverse('global_search'), {'q': 'Evento'})
        self.assertEqual([r['title'] for r in ricerca.json()['results']], ['Evento mio'])


class DiarioCondivisioneTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        from datetime import datetime
        from django.utils import timezone
        from diario.models import Diario
        User = get_user_model()
        self.altro = User.objects.create_user('altro', password='x')
        self.terzo = User.objects.create_user('terzo', password='x')
        oggi = timezone.localdate()
        self.giorno = (oggi.year, oggi.month, oggi.day)
        quando = timezone.make_aware(datetime(oggi.year, oggi.month, oggi.day, 12, 0))
        nuova = lambda titolo, utente: Diario.objects.create(
            titolo=titolo, contenuto='testo', data_creazione=quando, owner=utente)
        self.mia = nuova('Mia', self.user)
        self.privata_altrui = nuova('Privata altrui', self.altro)
        self.con_me = nuova('Condivisa con me', self.altro)
        self.con_me.condiviso_con.add(self.user)
        self.con_terzo = nuova('Condivisa con terzo', self.altro)
        self.con_terzo.condiviso_con.add(self.terzo)

    def test_lista_e_giorno_mostrano_mie_e_condivise_con_me(self):
        lista = self.client.get(reverse('diario:diario_list'))
        self.assertEqual({d.titolo for d in lista.context['diari']}, {'Mia', 'Condivisa con me'})
        giorno = self.client.get(reverse('diario:diario_del_giorno', args=self.giorno))
        self.assertEqual({n.titolo for n in giorno.context['note']}, {'Mia', 'Condivisa con me'})

    def test_note_non_condivise_con_me_non_si_aprono(self):
        for nota in (self.privata_altrui, self.con_terzo):
            for nome in ['dettaglio_diario', 'scarica_nota_pdf', 'aggiorna_diario', 'cancella_diario']:
                with self.subTest(nota=nota.titolo, vista=nome):
                    risposta = self.client.get(reverse('diario:' + nome, args=[nota.pk]))
                    self.assertEqual(risposta.status_code, 404)

    def test_nota_condivisa_con_me_si_legge_ma_non_si_tocca(self):
        from diario.models import Diario
        pk = self.con_me.pk
        self.assertEqual(self.client.get(reverse('diario:dettaglio_diario', args=[pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('diario:scarica_nota_pdf', args=[pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('diario:aggiorna_diario', args=[pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('diario:cancella_diario', args=[pk])).status_code, 404)
        self.assertTrue(Diario.objects.filter(pk=pk).exists())

    def test_creare_una_nota_condivisa(self):
        from diario.models import Diario
        self.client.post(reverse('diario:nuovo_diario', args=self.giorno),
                         {'titolo': 'Nuova', 'contenuto': 'x', 'condiviso_con': [self.altro.pk]})
        nota = Diario.objects.get(titolo='Nuova')
        self.assertEqual(nota.owner, self.user)
        self.assertEqual(list(nota.condiviso_con.all()), [self.altro])

    def test_modificare_la_condivisione(self):
        self.client.post(reverse('diario:aggiorna_diario', args=[self.mia.pk]),
                         {'titolo': 'Mia', 'contenuto': 'testo', 'condiviso_con': [self.terzo.pk]})
        self.assertEqual(list(self.mia.condiviso_con.all()), [self.terzo])

    def test_il_form_non_offre_me_stesso(self):
        risposta = self.client.get(reverse('diario:nuovo_diario', args=self.giorno))
        utenti = risposta.context['form'].fields['condiviso_con'].queryset
        self.assertNotIn(self.user, utenti)
        self.assertIn(self.altro, utenti)


class ProcedureCondiviseTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.altro = get_user_model().objects.create_user('altro', password='x')
        self.mia = Procedura.objects.create(nome='Mia', cliente=self.cliente, owner=self.user)
        self.altrui = Procedura.objects.create(nome='Altrui', cliente=self.cliente, owner=self.altro)
        self.step_mio = Step.objects.create(procedura=self.mia, titolo='Mio step', corpo='x')
        self.step_altrui = Step.objects.create(procedura=self.altrui, titolo='Step altrui', corpo='x')

    def test_la_lista_mostra_tutte_le_procedure(self):
        risposta = self.client.get(reverse('procedura-list'))
        self.assertEqual({p.nome for p in risposta.context['procedure']}, {'Mia', 'Altrui'})

    def test_posso_leggere_procedura_e_step_altrui(self):
        self.assertEqual(self.client.get(reverse('procedura-detail', args=[self.altrui.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('step-detail', args=[self.step_altrui.pk])).status_code, 200)

    def test_non_posso_modificare_o_eliminare_procedura_altrui(self):
        for nome in ['procedura-update', 'procedura-delete']:
            url = reverse(nome, args=[self.altrui.pk])
            with self.subTest(vista=nome):
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(url, {'nome': 'X', 'cliente': self.cliente.pk}).status_code, 404)
        self.altrui.refresh_from_db()
        self.assertEqual(self.altrui.nome, 'Altrui')

    def test_non_posso_toccare_gli_step_altrui(self):
        url_nuovo = reverse('step-create', args=[self.altrui.pk])
        self.assertEqual(self.client.get(url_nuovo).status_code, 404)
        self.assertEqual(self.client.post(url_nuovo, {'titolo': 'N', 'corpo': 'x'}).status_code, 404)
        for nome in ['step-update', 'step-delete']:
            with self.subTest(vista=nome):
                self.assertEqual(self.client.get(reverse(nome, args=[self.step_altrui.pk])).status_code, 404)
        self.client.post(reverse('step-delete', args=[self.step_altrui.pk]))
        self.assertTrue(Step.objects.filter(pk=self.step_altrui.pk).exists())
        self.assertFalse(Step.objects.filter(titolo='N').exists())

    def test_non_posso_riordinare_gli_step_altrui(self):
        altro_step = Step.objects.create(procedura=self.altrui, titolo='B', corpo='x')
        ordine_prima = list(Step.objects.filter(procedura=self.altrui).values_list('pk', 'ordine'))
        risposta = self.client.post(
            reverse('update-step-order'),
            data=json.dumps({'step_order': [altro_step.pk, self.step_altrui.pk]}),
            content_type='application/json',
        )
        self.assertEqual(risposta.status_code, 400)
        self.assertEqual(list(Step.objects.filter(procedura=self.altrui).values_list('pk', 'ordine')), ordine_prima)

    def test_posso_gestire_le_mie(self):
        self.client.post(reverse('procedura-update', args=[self.mia.pk]),
                         {'nome': 'Rinominata', 'cliente': self.cliente.pk})
        self.mia.refresh_from_db()
        self.assertEqual(self.mia.nome, 'Rinominata')
        self.client.post(reverse('step-create', args=[self.mia.pk]), {'titolo': 'Nuovo', 'corpo': 'x'})
        self.assertTrue(Step.objects.filter(procedura=self.mia, titolo='Nuovo').exists())
        self.client.post(reverse('procedura-delete', args=[self.mia.pk]))
        self.assertFalse(Procedura.objects.filter(pk=self.mia.pk).exists())

    def test_non_posso_spostare_uno_step_in_una_procedura_altrui(self):
        risposta = self.client.get(reverse('step-update', args=[self.step_mio.pk]))
        scelte = risposta.context['form'].fields['procedura'].queryset
        self.assertIn(self.mia, scelte)
        self.assertNotIn(self.altrui, scelte)


class PasswordESessioneTests(BaseTestCase):
    def test_la_pagina_cambio_password_si_apre(self):
        self.assertEqual(self.client.get(reverse('password_change')).status_code, 200)

    def test_cambio_password_riuscito_e_resto_collegato(self):
        nuova = 'Nuova-Password-2026'
        risposta = self.client.post(reverse('password_change'), {
            'old_password': 'x', 'new_password1': nuova, 'new_password2': nuova,
        })
        self.assertRedirects(risposta, reverse('password_change_done'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(nuova))
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def test_password_attuale_sbagliata(self):
        nuova = 'Nuova-Password-2026'
        risposta = self.client.post(reverse('password_change'), {
            'old_password': 'sbagliata', 'new_password1': nuova, 'new_password2': nuova,
        })
        self.assertEqual(risposta.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('x'))

    def test_la_sessione_dura_14_giorni(self):
        from django.conf import settings
        self.assertEqual(settings.SESSION_COOKIE_AGE, 14 * 24 * 60 * 60)


class HomeLavoroTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        from datetime import timedelta
        self.altro = get_user_model().objects.create_user('altro', password='x')
        richiedente = Richiedente.objects.create(nome='Mario', cognome='Rossi', cliente=self.cliente)
        categoria = Categoria.objects.create(nome='Test')
        crea = lambda nome, utente, stato='aperta': Attivita.objects.create(
            nome_flusso=nome, richiedente=richiedente, categoria=categoria, owner=utente, stato=stato)
        crea('Mia aperta', self.user)
        crea('Mia chiusa', self.user, 'chiusa')
        crea('Altrui aperta', self.altro)
        oggi = date.today()
        task = lambda titolo, giorno, utente: Task.objects.create(
            title=titolo, data_creazione=giorno, owner=utente)
        task('Task oggi', oggi, self.user)
        task('Task in ritardo', oggi - timedelta(days=2), self.user)
        task('Task domani', oggi + timedelta(days=1), self.user)
        task('Task altrui', oggi, self.altro)
        dati = dict(cliente=self.cliente, data=oggi, ambiente='Test', livello='basso', occorrenze=1)
        Errore.objects.create(owner=self.user, **dati)
        Errore.objects.create(owner=self.altro, **dati)

    def test_attivita_aperte_solo_mie(self):
        home = self.client.get(reverse('home'))
        self.assertEqual([a.nome_flusso for a in home.context['attivita_aperte']], ['Mia aperta'])
        self.assertEqual(home.context['totale_attivita_aperte'], 1)

    def test_todo_di_oggi_e_in_ritardo_solo_miei(self):
        home = self.client.get(reverse('home'))
        titoli = {t.title for t in home.context['task_da_fare']}
        self.assertEqual(titoli, {'Task oggi', 'Task in ritardo'})
        self.assertEqual(home.context['totale_task_da_fare'], 2)
        self.assertEqual(home.context['task_in_ritardo'], 1)

    def test_errori_solo_miei(self):
        home = self.client.get(reverse('home'))
        self.assertEqual(home.context['totale_errori'], 1)
        self.assertEqual(len(home.context['errori_recenti']), 1)
