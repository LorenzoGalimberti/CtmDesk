from datetime import date

def aggiungi_data_corrente(request):
    return {
        'today': date.today()  # Ritorna la data corrente
    }
