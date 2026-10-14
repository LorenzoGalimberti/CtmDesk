# CTMDesk

Gestionale personale in Django per organizzare il lavoro quotidiano: attività, to-do, diario,
calendario, registro errori, procedure e piccoli strumenti di utilità.

## Moduli

| App | Cosa fa |
|---|---|
| `core` | Home con dashboard (eventi di oggi, prossimi eventi, statistiche) e modello `Cliente` |
| `activities` | Attività con richiedente, categoria, stato aperta/chiusa, note e allegati |
| `todo` | Lista di task, manuali o generati dalle attività, con filtri e archiviazione |
| `diario` | Note giornaliere con editor Summernote, tag, clienti ed export in PDF |
| `calendario` | Eventi per cliente, vista calendario e lista |
| `errors` | Registro degli errori per cliente, con livello e occorrenze |
| `procedura` | Procedure composte da passi ordinabili, con immagini |
| `tools` | Strumenti di utilità, tra cui l'analisi degli impatti/fermi da file Excel |

Le attività e i task sono collegati: creare un'attività apre un task, e chiudere
l'attività completa i task associati (e viceversa).

## Requisiti

- Python 3.12 o superiore
- Git

## Installazione

```bash
git clone https://github.com/LorenzoGalimberti/CtmDesk.git
cd CtmDesk

python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash)
# source venv/bin/activate        # Linux / macOS

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Poi apri http://127.0.0.1:8000/ nel browser. L'area di amministrazione è su `/admin/`.

## Dati

Il database (`db.sqlite3`) e i file caricati (`media/`) non fanno parte del repository:
al primo avvio il database è vuoto e va creato con `migrate`.

## Stato del progetto

Progetto in sviluppo. Alcune parti sono incomplete o in corso di sistemazione
(per esempio `email_center`, non ancora collegato all'interfaccia, e l'app
`procedure`, un duplicato storico di `procedura` che verrà rimosso).
