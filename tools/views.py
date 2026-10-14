from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, timedelta
import pandas as pd
import os
from django.conf import settings
import tempfile
import logging
import sys

# Configura il logger
logger = logging.getLogger(__name__)

def index(request):
    """Vista principale per la pagina dei tools"""
    return render(request, 'index.html')

def impatti_fermi(request):
    """Tool per analizzare i fermi in un intervallo di date e ore"""
    
    # Funzione di debug per stampare informazioni dettagliate
    def debug_print(label, value):
        print(f"DEBUG [{label}]: {value}", file=sys.stderr)
    
    context = {
        'title': 'Analisi Impatti Fermi',
        'date_error': None,
        'data': None,
        'processed_file': None,
        'data_selezionata': None,
        'ora_inizio': None,
        'ora_fine': None,
        'debug_info': None,  # Aggiungiamo info di debug
    }
    
    debug_print("Request method", request.method)
    
    if request.method == 'POST':
        # Ottieni i parametri dalla richiesta
        data_selezionata = request.POST.get('data_selezionata')
        ora_inizio = request.POST.get('ora_inizio')
        ora_fine = request.POST.get('ora_fine')
        uploaded_file = request.FILES.get('file_excel')
        
        debug_print("Parameters", f"data_selezionata={data_selezionata}, ora_inizio={ora_inizio}, ora_fine={ora_fine}")
        debug_print("File uploaded", bool(uploaded_file))
        
        # Validazione dei dati
        if not data_selezionata:
            context['date_error'] = 'La data è obbligatoria'
            return render(request, 'impatti_fermi.html', context)
        
        if not ora_inizio or not ora_fine:
            context['date_error'] = 'È necessario specificare sia l\'ora di inizio che l\'ora di fine'
            return render(request, 'impatti_fermi.html', context)
        
        try:
            # Parsing della data selezionata e degli orari
            debug_print("Parsing data_selezionata", data_selezionata)
            data_selezionata_obj = datetime.strptime(data_selezionata, '%Y-%m-%d')
            debug_print("data_selezionata_obj", data_selezionata_obj)
            
            # Parsing degli orari
            debug_print("Parsing ora_inizio", ora_inizio)
            ora_inizio_obj = datetime.strptime(ora_inizio, '%H:%M').time()
            debug_print("ora_inizio_obj", ora_inizio_obj)
            
            debug_print("Parsing ora_fine", ora_fine)
            ora_fine_obj = datetime.strptime(ora_fine, '%H:%M').time()
            debug_print("ora_fine_obj", ora_fine_obj)
            
            # Carica il file Excel
            if uploaded_file:
                # Crea un file temporaneo per salvare l'Excel caricato
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    tmp.write(uploaded_file.read())
                    temp_file_path = tmp.name
                    debug_print("Temp file path", temp_file_path)
                
                try:
                    # Apri il file Excel
                    debug_print("Reading Excel file", "Starting")
                    df = pd.read_excel(temp_file_path)
                    debug_print("Excel file loaded", f"Shape: {df.shape}")
                    
                    # Debug info
                    debug_print("Columns in file", list(df.columns))
                    
                    # Determina il formato del file analizzando le colonne
                    formato1 = 'Estimated End Time' in df.columns and 'Order Date' in df.columns
                    formato2 = 'Start Exec' in df.columns and 'End Exec' in df.columns
                    
                    debug_print("File format 1 (Estimated End Time)", formato1)
                    debug_print("File format 2 (Start/End Exec)", formato2)
                    
                    if formato1:
                        # Primo formato con "Estimated End Time" e "Order Date"
                        est_end_col = 'Estimated End Time'
                        order_date_col = 'Order Date'
                        
                        # Converti la colonna Estimated End Time in datetime
                        if not pd.api.types.is_datetime64_any_dtype(df[est_end_col]):
                            debug_print("Converting Estimated End Time", "Starting")
                            try:
                                df[est_end_col] = pd.to_datetime(df[est_end_col], format='%d/%m/%Y %H:%M', errors='coerce')
                            except Exception as e:
                                debug_print("Conversion error 1", str(e))
                                try:
                                    df[est_end_col] = pd.to_datetime(df[est_end_col], dayfirst=True, errors='coerce')
                                except Exception as e2:
                                    debug_print("Conversion error 2", str(e2))
                        
                        # Converti la colonna Order Date in datetime
                        if not pd.api.types.is_datetime64_any_dtype(df[order_date_col]):
                            debug_print("Converting Order Date", "Starting")
                            try:
                                df[order_date_col] = pd.to_datetime(df[order_date_col], format='%d/%m/%Y', errors='coerce')
                            except Exception as e:
                                debug_print("Conversion error 1", str(e))
                                try:
                                    df[order_date_col] = pd.to_datetime(df[order_date_col], dayfirst=True, errors='coerce')
                                except Exception as e2:
                                    debug_print("Conversion error 2", str(e2))
                        
                        # 1. Crea il filtro per Order Date uguale alla data selezionata
                        df['order_date_day'] = df[order_date_col].dt.date
                        order_date_mask = (df['order_date_day'] == data_selezionata_obj.date())
                        
                        # 2. Estrai il tempo dall'Estimated End Time per il filtro orario
                        df['end_date'] = df[est_end_col].dt.date
                        df['end_time'] = df[est_end_col].dt.time
                        
                        # Crea il filtro per l'intervallo orario di Estimated End Time
                        if ora_inizio_obj < ora_fine_obj:
                            # Caso normale: es. dalle 8:00 alle 16:00
                            time_mask = (df['end_time'] >= ora_inizio_obj) & (df['end_time'] <= ora_fine_obj)
                        else:
                            # Caso in cui l'intervallo attraversa la mezzanotte: es. dalle 22:00 alle 6:00
                            time_mask = (df['end_time'] >= ora_inizio_obj) | (df['end_time'] <= ora_fine_obj)
                        
                        # Combiniamo i filtri
                        mask = order_date_mask & time_mask
                        
                        # Colonne da visualizzare
                        columns_to_display = ['Name', 'Estimated Start Time', 'Estimated End Time']
                        
                    elif formato2:
                        # Secondo formato con "Start Exec" e "End Exec"
                        start_exec_col = 'Start Exec'
                        end_exec_col = 'End Exec'
                        
                        # Converti le colonne di data/ora
                        for col in [start_exec_col, end_exec_col]:
                            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                                debug_print(f"Converting {col}", "Starting")
                                try:
                                    df[col] = pd.to_datetime(df[col], format='%d/%m/%Y %H:%M', errors='coerce')
                                except Exception as e:
                                    debug_print(f"Conversion error for {col} (1)", str(e))
                                    try:
                                        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
                                    except Exception as e2:
                                        debug_print(f"Conversion error for {col} (2)", str(e2))
                        
                        # Estrai data e ora da End Exec
                        df['end_date'] = df[end_exec_col].dt.date
                        df['end_time'] = df[end_exec_col].dt.time
                        
                        # Filtro per data
                        date_mask = (df['end_date'] == data_selezionata_obj.date())
                        
                        # Filtro per ora
                        if ora_inizio_obj < ora_fine_obj:
                            time_mask = (df['end_time'] >= ora_inizio_obj) & (df['end_time'] <= ora_fine_obj)
                        else:
                            time_mask = (df['end_time'] >= ora_inizio_obj) | (df['end_time'] <= ora_fine_obj)
                        
                        # Combiniamo i filtri
                        mask = date_mask & time_mask
                        
                        # Colonne da visualizzare (adattate al nuovo formato)
                        # Verifica quali colonne sono presenti nel file
                        available_columns = df.columns.tolist()
                        columns_to_display = []
                        
                        # Aggiungi colonne in base alla disponibilità
                        if 'Mem Name' in available_columns:
                            columns_to_display.append('Mem Name')
                        if 'Application' in available_columns:
                            columns_to_display.append('Application')
                        if 'Sub Application' in available_columns:
                            columns_to_display.append('Sub Application')
                        
                        # Aggiungi sempre le colonne di data/ora
                        columns_to_display.extend([start_exec_col, end_exec_col])
                    
                    else:
                        # Formato non riconosciuto
                        context['date_error'] = 'Formato del file non riconosciuto. Il file deve contenere "Estimated End Time" e "Order Date" oppure "Start Exec" e "End Exec".'
                        return render(request, 'impatti_fermi.html', context)
                    
                    # Applica il filtro al DataFrame
                    filtered_df = df[mask].copy()
                    filtered_count = len(filtered_df)
                    debug_print("Final filtered count", filtered_count)
                    
                    # Verifica se ci sono risultati
                    if not filtered_df.empty:
                        # Filtra le colonne da visualizzare (se esistono nel DataFrame)
                        columns_to_display = [col for col in columns_to_display if col in filtered_df.columns]
                        filtered_df = filtered_df[columns_to_display]
                        
                        # Converti il DataFrame in HTML per la visualizzazione
                        html_table = filtered_df.to_html(classes='table table-striped table-bordered table-hover', 
                                                        index=False, escape=False, na_rep='')
                        
                        # Calcola l'intervallo orario per la visualizzazione
                        ora_inizio_dt = datetime.strptime(ora_inizio, '%H:%M')
                        ora_fine_dt = datetime.strptime(ora_fine, '%H:%M')
                        
                        if ora_inizio_dt < ora_fine_dt:
                            intervallo_ore = (ora_fine_dt - ora_inizio_dt).seconds / 3600
                        else:
                            # Caso di attraversamento della mezzanotte
                            ora_fine_dt_next_day = ora_fine_dt + timedelta(days=1)
                            intervallo_ore = (ora_fine_dt_next_day - ora_inizio_dt).seconds / 3600
                        
                        # Aggiorna il contesto con i dati filtrati
                        context.update({
                            'data': html_table,
                            'conteggio_righe': len(filtered_df),
                            'data_selezionata': data_selezionata,
                            'ora_inizio': ora_inizio,
                            'ora_fine': ora_fine,
                            'intervallo_ore': round(intervallo_ore, 1),
                            'processed_file': uploaded_file.name,
                        })
                        debug_print("Results found", "Success")
                    else:
                        context.update({
                            'data': '<p class="alert alert-warning">Nessun job trovato per la data selezionata' + 
                                   ' nell\'intervallo orario specificato.</p>',
                            'data_selezionata': data_selezionata,
                            'ora_inizio': ora_inizio,
                            'ora_fine': ora_fine,
                            'processed_file': uploaded_file.name,
                        })
                        debug_print("Results found", "No matches")
                
                finally:
                    # Rimuovi il file temporaneo
                    debug_print("Removing temp file", temp_file_path)
                    os.unlink(temp_file_path)
            else:
                context['date_error'] = 'Devi caricare un file Excel'
                debug_print("Error", "No file uploaded")
        
        except ValueError as e:
            context['date_error'] = f'Errore nel formato della data o nell\'intervallo: {str(e)}'
            debug_print("ValueError", str(e))
        except Exception as e:
            context['date_error'] = f'Errore durante l\'elaborazione: {str(e)}'
            debug_print("Exception", str(e))
    
    return render(request, 'impatti_fermi.html', context)