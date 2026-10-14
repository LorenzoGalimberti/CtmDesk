from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import DiarioForm
from .models import Diario
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Q

# Importazioni per il PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import re
import html

def diario_list(request):
    query = request.GET.get('q')  # Ottieni il parametro di ricerca
    diari = Diario.objects.all().order_by('-data_creazione')  # Recupera tutti i diari

    if query:  # Se esiste una query
        diari = diari.filter(
            Q(titolo__icontains=query) |  # Cerca nei titoli
            Q(contenuto__icontains=query)  # Cerca nei contenuti
        )

    today = date.today()  # Ottieni la data corrente
    return render(request, 'diario_list.html', {'diari': diari, 'today': today, 'query': query})


def nuovo_diario(request, anno, mese, giorno):
    giorno_naive = datetime(anno, mese, giorno, 0, 0, 0)
    giorno_corrente = timezone.make_aware(giorno_naive)

    if request.method == 'POST':
        form = DiarioForm(request.POST)
        if form.is_valid():
            diario = form.save(commit=False)
            diario.data_creazione = giorno_corrente
            diario.save()
            # Salva le relazioni Many-to-Many (tag e clienti)
            form.save_m2m()
            return redirect('diario:diario_del_giorno', anno=anno, mese=mese, giorno=giorno)
    else:
        form = DiarioForm()

    return render(request, 'nuovo_diario.html', {'form': form, 'giorno': giorno_corrente})


def diario_del_giorno(request, anno, mese, giorno):
    # Crea una data naive
    giorno_naive = datetime(anno, mese, giorno)
    
    # Converti in data timezone-aware
    giorno_corrente = timezone.make_aware(giorno_naive)

    # Filtra le note per quel giorno
    note = Diario.objects.filter(
        data_creazione__gte=giorno_corrente,
        data_creazione__lt=giorno_corrente + timedelta(days=1)
    )

    # Calcola la data precedente e successiva (timezone-aware)
    giorno_precedente = giorno_corrente - timedelta(days=1)
    giorno_successivo = giorno_corrente + timedelta(days=1)

    return render(request, 'diario_del_giorno.html', {
        'giorno': giorno_corrente.date(),  # Puoi passare solo la parte della data
        'note': note,
        'giorno_precedente': giorno_precedente.date(),
        'giorno_successivo': giorno_successivo.date(),
    })


def dettaglio_diario(request, pk):
    nota = get_object_or_404(Diario, pk=pk)
    today = date.today()  # Aggiungi la data corrente al contesto

    return render(request, 'dettaglio_diario.html', {'nota': nota, 'today': today})


def aggiorna_diario(request, pk):
    nota = get_object_or_404(Diario, pk=pk)
    
    if request.method == 'POST':
        form = DiarioForm(request.POST, instance=nota)
        if form.is_valid():
            # Salva la nota senza salvare subito le relazioni Many-to-Many
            diario = form.save(commit=False)
            
            # Ottieni i clienti selezionati dal form
            selected_clienti = form.cleaned_data['clienti']
            
            # Rimuovi i clienti non selezionati (relazione Many-to-Many)
            nota.clienti.clear()  # Rimuovi tutti i clienti precedenti
            nota.clienti.add(*selected_clienti)  # Aggiungi i nuovi clienti selezionati
            
            diario.save()  # Salva la nota con le relazioni aggiornate
            return redirect('diario:dettaglio_diario', pk=nota.pk)
    else:
        form = DiarioForm(instance=nota)

    return render(request, 'aggiorna_diario.html', {'form': form, 'nota': nota})


def cancella_diario(request, pk):
    nota = get_object_or_404(Diario, pk=pk)  # Recupera la nota da cancellare

    # Salva la data della nota per il redirect
    data_creazione = nota.data_creazione
    nota.delete()  # Elimina la nota

    # Redirect alla pagina del diario del giorno
    return redirect('diario:diario_del_giorno', 
                    anno=data_creazione.year, 
                    mese=data_creazione.month, 
                    giorno=data_creazione.day)


def scarica_nota_pdf(request, pk):
    """Vista per scaricare la nota come PDF con formattazione HTML"""
    nota = get_object_or_404(Diario, pk=pk)
    
    # Crea la risposta HTTP per il PDF
    response = HttpResponse(content_type='application/pdf')
    # Pulisci il titolo per il nome del file
    titolo_pulito = re.sub(r'[^\w\s-]', '', nota.titolo)
    response['Content-Disposition'] = f'attachment; filename="nota_{nota.id}_{titolo_pulito[:30]}.pdf"'
    
    # Crea il documento PDF
    doc = SimpleDocTemplate(response, pagesize=A4,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=50)
    
    # Elementi del documento
    elements = []
    
    # Stili base
    styles = getSampleStyleSheet()
    
    # Stili personalizzati
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=HexColor('#2c3e50'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Oblique'
    )
    
    client_style = ParagraphStyle(
        'ClientStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#3498db'),
        spaceAfter=15,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    
    # Stili per il contenuto con formattazione
    normal_style = ParagraphStyle(
        'NormalContent',
        parent=styles['Normal'],
        fontSize=12,
        leading=18,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=6,
        fontName='Helvetica'
    )
    
    # Aggiungi titolo
    elements.append(Paragraph(html.escape(nota.titolo), title_style))
    
    # Aggiungi data
    data_formattata = nota.data_creazione.strftime("%d %B %Y alle %H:%M")
    elements.append(Paragraph(f"Creata il: {data_formattata}", date_style))
    
    # Aggiungi spazio
    elements.append(Spacer(1, 20))
    
    # Aggiungi clienti se presenti
    if nota.clienti.exists():
        clienti_text = "Clienti associati: " + ", ".join([cliente.nome for cliente in nota.clienti.all()])
        elements.append(Paragraph(html.escape(clienti_text), client_style))
        elements.append(Spacer(1, 15))
    
    # Aggiungi linea separatrice
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#bdc3c7')))
    elements.append(Spacer(1, 20))
    
    # Processa il contenuto HTML
    contenuto_formattato = processa_html_per_pdf(nota.contenuto, normal_style)
    
    # Aggiungi ogni elemento del contenuto
    for elemento in contenuto_formattato:
        elements.append(elemento)
    
    # Costruisci il PDF
    doc.build(elements)
    
    return response


def processa_html_per_pdf(html_content, base_style):
    """
    Processa il contenuto HTML e lo converte in elementi ReportLab mantenendo la formattazione
    """
    if not html_content:
        return [Paragraph("Contenuto vuoto", base_style)]
    
    elements = []
    
    # Pulisci il contenuto
    content = html_content.strip()
    
    # Prima di tutto, rimuovi i tag <para> e simili che causano problemi
    content = rimuovi_tag_problematici(content)
    
    # Gestisci i tag <hr> (linee orizzontali)
    content = re.sub(r'<hr[^>]*>', '|||HR|||', content, flags=re.IGNORECASE)
    
    # Gestisci i tag <br> (a capo)
    content = re.sub(r'<br[^>]*>', '<br/>', content, flags=re.IGNORECASE)
    
    # Dividi il contenuto in blocchi separati da HR
    blocchi = content.split('|||HR|||')
    
    for i, blocco in enumerate(blocchi):
        if i > 0:  # Aggiungi HR prima di ogni blocco tranne il primo
            elements.append(Spacer(1, 10))
            elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#bdc3c7')))
            elements.append(Spacer(1, 10))
        
        # Processa ogni blocco
        elementi_blocco = processa_blocco_html(blocco.strip(), base_style)
        elements.extend(elementi_blocco)
    
    return elements if elements else [Paragraph("Contenuto non disponibile", base_style)]


def rimuovi_tag_problematici(html_content):
    """
    Rimuove i tag HTML che causano problemi con ReportLab
    """
    # Rimuovi tag <para> che causano problemi
    html_content = re.sub(r'<para[^>]*>', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'</para>', '', html_content, flags=re.IGNORECASE)
    
    # Rimuovi attributi face con font non supportati dai tag font
    html_content = re.sub(
        r'<font([^>]*)\s+face="[^"]*"([^>]*)>', 
        r'<font\1\2>', 
        html_content, 
        flags=re.IGNORECASE
    )
    
    # Rimuovi attributi style complessi
    html_content = re.sub(
        r'<font([^>]*)\s+style="[^"]*"([^>]*)>', 
        r'<font\1\2>', 
        html_content, 
        flags=re.IGNORECASE
    )
    
    return html_content


def processa_blocco_html(blocco, base_style):
    """
    Processa un singolo blocco di HTML
    """
    if not blocco.strip():
        return []
    
    elements = []
    
    # Gestisci i paragrafi
    paragrafi = re.split(r'<p[^>]*>|</p>', blocco, flags=re.IGNORECASE)
    paragrafi = [p.strip() for p in paragrafi if p.strip()]
    
    if not paragrafi:
        # Se non ci sono tag <p>, tratta tutto come un unico paragrafo
        paragrafi = [blocco]
    
    for paragrafo in paragrafi:
        if not paragrafo.strip():
            continue
            
        # Gestisci i titoli
        if re.search(r'<h[1-6][^>]*>', paragrafo, re.IGNORECASE):
            elemento = processa_titolo(paragrafo, base_style)
            if elemento:
                elements.append(elemento)
                continue
        
        # Gestisci i paragrafi normali con formattazione
        elemento = processa_paragrafo_formattato(paragrafo, base_style)
        if elemento:
            elements.append(elemento)
    
    return elements


def processa_titolo(html_text, base_style):
    """
    Processa i tag di titolo (h1, h2, etc.)
    """
    # Trova il tag di titolo
    match = re.search(r'<h([1-6])[^>]*>(.*?)</h[1-6]>', html_text, re.IGNORECASE | re.DOTALL)
    if match:
        livello = int(match.group(1))
        testo = match.group(2)
        
        # Rimuovi altri tag HTML dal testo
        testo = re.sub(r'<[^>]+>', '', testo)
        testo = html.unescape(testo).strip()
        
        if testo:
            # Crea uno stile per il titolo basato sul livello
            font_size = max(16 - (livello - 1) * 2, 12)
            
            heading_style = ParagraphStyle(
                f'Heading{livello}',
                parent=base_style,
                fontSize=font_size,
                fontName='Helvetica-Bold',
                textColor=HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=18 if livello <= 2 else 12
            )
            
            return Paragraph(html.escape(testo), heading_style)
    
    return None


def processa_paragrafo_formattato(html_text, base_style):
    """
    Processa un paragrafo mantenendo la formattazione interna (bold, italic, etc.)
    """
    if not html_text.strip():
        return None
    
    # Converti il testo HTML in formato ReportLab
    testo_convertito = converti_html_a_reportlab(html_text)
    
    if testo_convertito.strip():
        try:
            return Paragraph(testo_convertito, base_style)
        except Exception as e:
            # Se c'è un errore, restituisci una versione semplificata
            testo_semplice = re.sub(r'<[^>]+>', '', html_text)
            testo_semplice = html.unescape(testo_semplice).strip()
            if testo_semplice:
                return Paragraph(html.escape(testo_semplice), base_style)
    
    return None


def converti_html_a_reportlab(html_text):
    """
    Converte tag HTML comuni in markup ReportLab compatibile
    """
    # Prima pulisci il testo da tag problematici
    testo = rimuovi_tag_problematici(html_text)
    
    # Mappa dei tag HTML ai tag ReportLab (solo quelli sicuri)
    conversioni = [
        # Grassetto - mantieni solo il contenuto in <b>
        (r'<strong[^>]*>(.*?)</strong>', r'<b>\1</b>'),
        (r'<b[^>]*>(.*?)</b>', r'<b>\1</b>'),
        
        # Corsivo
        (r'<em[^>]*>(.*?)</em>', r'<i>\1</i>'),
        (r'<i[^>]*>(.*?)</i>', r'<i>\1</i>'),
        
        # Sottolineato
        (r'<u[^>]*>(.*?)</u>', r'<u>\1</u>'),
        
        # A capo
        (r'<br[^>]*/?>', '<br/>'),
        
        # Rimuovi tag font con attributi complessi e mantieni solo il contenuto
        (r'<font[^>]*color\s*=\s*["\']([^"\']*)["\'][^>]*>(.*?)</font>', r'<font color="\1">\2</font>'),
        (r'<font[^>]*>(.*?)</font>', r'\1'),  # Rimuovi font senza colore
        
        # Link (mantieni solo il testo)
        (r'<a[^>]*>(.*?)</a>', r'\1'),
        
        # Span (mantieni solo il contenuto)
        (r'<span[^>]*>(.*?)</span>', r'\1'),
        
        # Lista non ordinata
        (r'<ul[^>]*>', ''),
        (r'</ul>', ''),
        (r'<li[^>]*>(.*?)</li>', r'• \1<br/>'),
        
        # Lista ordinata
        (r'<ol[^>]*>', ''),
        (r'</ol>', ''),
        
        # Div e altri contenitori
        (r'<div[^>]*>', ''),
        (r'</div>', ''),
        (r'<p[^>]*>', ''),
        (r'</p>', '<br/>'),
        
        # Rimuovi altri tag non supportati
        (r'<[^>]*>', ''),
    ]
    
    # Applica tutte le conversioni
    for pattern, replacement in conversioni:
        testo = re.sub(pattern, replacement, testo, flags=re.IGNORECASE | re.DOTALL)
    
    # Pulisci spazi multipli e a capo
    testo = re.sub(r'\s+', ' ', testo)
    testo = testo.replace('<br/> ', '<br/>')
    testo = re.sub(r'(<br/>){3,}', '<br/><br/>', testo)
    
    # Decodifica entità HTML
    testo = html.unescape(testo)
    
    # Validazione finale: rimuovi qualsiasi tag rimasto che non sia supportato
    tag_supportati_pattern = r'<(?!/?(?:b|i|u|br|font)\b)[^>]*>'
    testo = re.sub(tag_supportati_pattern, '', testo, flags=re.IGNORECASE)
    
    return testo.strip()