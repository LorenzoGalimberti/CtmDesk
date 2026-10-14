# email_integration/services.py
import imaplib
import email
from email.header import decode_header
import re
import html
from datetime import datetime
import logging
from django.utils import timezone

from todo.models import Task
from .models import ImportedEmail

logger = logging.getLogger(__name__)

class EmailService:
    """
    Servizio per interagire con una casella di posta elettronica via IMAP.
    """
    def __init__(self, email_address, password, imap_server='imap.gmail.com', imap_port=993):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
    
    def connect(self):
        """
        Crea una connessione al server IMAP.
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.password)
            return mail
        except imaplib.IMAP4.error as e:
            logger.error(f"Errore di connessione IMAP: {str(e)}")
            raise ConnectionError(f"Impossibile connettersi al server IMAP: {str(e)}")
    
    def list_labels(self):
        """
        Elenca tutte le etichette/cartelle disponibili.
        """
        mail = self.connect()
        try:
            status, mailboxes = mail.list()
            if status != 'OK':
                raise Exception("Impossibile recuperare l'elenco delle mailbox")
            
            labels = []
            for mailbox in mailboxes:
                # Estrai il nome della mailbox
                parts = mailbox.decode().split(' "')
                if len(parts) > 1:
                    label_name = parts[-1].strip('"')
                    labels.append(label_name)
            
            return sorted(labels)
        finally:
            mail.logout()
    
    def fetch_emails_by_label(self, label, max_emails=20, since_date=None):
        """
        Recupera le email da una specifica etichetta/cartella.
        
        Args:
            label: Nome dell'etichetta o cartella
            max_emails: Numero massimo di email da recuperare
            since_date: Se specificato, recupera solo le email più recenti di questa data
            
        Returns:
            Lista di dizionari con i dettagli delle email
        """
        mail = self.connect()
        
        try:
            # Per Gmail, le etichette sono accessibili con 'label/'
            # Prova prima il nome esatto dell'etichetta
            status, messages = mail.select(f'"{label}"')
            
            if status != 'OK':
                # Prova a trovare l'etichetta tra quelle disponibili
                status, mailboxes = mail.list()
                
                label_pattern = f'"{label}"'
                found = False
                for mailbox in mailboxes:
                    if label_pattern.lower() in mailbox.decode().lower():
                        # Estrai il nome della mailbox
                        match = re.search(r'"([^"]*)"$', mailbox.decode())
                        if match:
                            mailbox_name = match.group(1)
                            status, messages = mail.select(f'"{mailbox_name}"')
                            if status == 'OK':
                                found = True
                                break
                
                if not found:
                    # Prova con il formato di Gmail
                    status, messages = mail.select(f'"[Gmail]/{label}"')
                    if status != 'OK':
                        raise Exception(f"Impossibile trovare l'etichetta '{label}'")
            
            # Costruisci il criterio di ricerca
            search_criteria = ['ALL']
            if since_date:
                # Formatta la data nel formato "DD-MMM-YYYY" richiesto da IMAP
                date_str = since_date.strftime("%d-%b-%Y")
                search_criteria = ['SINCE', date_str]
            
            status, messages = mail.search(None, *search_criteria)
            if status != 'OK':
                raise Exception("Errore nella ricerca delle email")
            
            message_ids = messages[0].split()
            # Prendi gli ultimi N messaggi (più recenti)
            message_ids = message_ids[-max_emails:] if len(message_ids) > max_emails else message_ids
            
            emails = []
            for msg_id in message_ids:
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Decodifica l'oggetto
                subject = msg.get('Subject', '')
                decoded_subject = self._decode_header(subject)
                
                # Estrai il mittente
                from_addr = msg.get('From', '')
                decoded_from = self._decode_header(from_addr)
                
                # Estrai la data
                date_str = msg.get('Date', '')
                received_date = self._parse_date(date_str)
                
                # Estrai il corpo (testo o html)
                body = self._extract_body(msg)
                
                # Prendi i primi 1000 caratteri come anteprima
                snippet = body[:1000].strip() if body else ""
                
                # Estrai l'ID univoco del messaggio
                message_id = msg.get('Message-ID', '')
                
                emails.append({
                    'subject': decoded_subject,
                    'from': decoded_from,
                    'date': received_date,
                    'date_str': date_str,
                    'body': body,
                    'snippet': snippet,
                    'message_id': message_id,
                })
            
            return emails
        
        finally:
            mail.close()
            mail.logout()
    
    def _decode_header(self, header):
        """
        Decodifica l'intestazione dell'email.
        """
        if not header:
            return ""
            
        decoded_header = decode_header(header)
        result = ""
        for data, charset in decoded_header:
            if isinstance(data, bytes):
                result += data.decode(charset or 'utf-8', errors='replace')
            else:
                result += data
        return result
    
    def _extract_body(self, msg):
        """
        Estrae il corpo del messaggio, preferendo il testo semplice se disponibile.
        """
        body = ""
        if msg.is_multipart():
            # Prima cerca testo semplice
            text_part = None
            html_part = None
            
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Ignora gli allegati
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain" and not text_part:
                    text_part = part
                elif content_type == "text/html" and not html_part:
                    html_part = part
            
            # Usa testo semplice se disponibile, altrimenti html
            if text_part:
                body = text_part.get_payload(decode=True).decode(
                    text_part.get_content_charset() or 'utf-8', 
                    errors='replace'
                )
            elif html_part:
                html_body = html_part.get_payload(decode=True).decode(
                    html_part.get_content_charset() or 'utf-8', 
                    errors='replace'
                )
                body = html.unescape(re.sub('<[^<]+?>', '', html_body))
        else:
            # Non è multipart
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                body = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or 'utf-8', 
                    errors='replace'
                )
            elif content_type == "text/html":
                html_body = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or 'utf-8', 
                    errors='replace'
                )
                body = html.unescape(re.sub('<[^<]+?>', '', html_body))
        
        return body
    
    def _parse_date(self, date_str):
        """
        Converte una stringa di data da email nel formato datetime.
        """
        if not date_str:
            return timezone.now()
            
        # I formati delle date possono variare, prova diversi approcci
        try:
            # Prima prova email.utils.parsedate_to_datetime
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt
        except Exception:
            # Se fallisce, usa un approccio più semplice
            try:
                import dateutil.parser
                dt = dateutil.parser.parse(date_str)
                return dt
            except Exception:
                # Se anche questo fallisce, ritorna la data attuale
                return timezone.now()


class EmailImportService:
    """
    Servizio per l'importazione delle email come task.
    """
    def __init__(self, email_label):
        """
        Inizializza il servizio con un'etichetta email.
        
        Args:
            email_label: Istanza di EmailLabel
        """
        self.email_label = email_label
        self.config = email_label.config
        self.email_service = EmailService(
            self.config.email,
            self.config.password,
            self.config.imap_server,
            self.config.imap_port
        )
    
    def import_emails(self):
        """
        Importa le email dall'etichetta specificata e le converte in task.
        
        Returns:
            Tuple (int, int): (numero di email recuperate, numero di task creati)
        """
        # Determina la data dell'ultima importazione
        since_date = self.email_label.last_import or None
        
        try:
            # Recupera le email
            emails = self.email_service.fetch_emails_by_label(
                self.email_label.name,
                self.email_label.max_emails,
                since_date
            )
            
            # Converti le email in task
            created_count = 0
            for email_data in emails:
                # Verifica se l'email è già stata importata
                if ImportedEmail.objects.filter(message_id=email_data['message_id']).exists():
                    continue
                
                # Crea un nuovo task
                task = Task.objects.create(
                    title=email_data['subject'] or 'Email senza oggetto',
                    description=f"Da: {email_data['from']}\n\n{email_data['snippet']}...",
                    priority=self.email_label.import_as_priority,
                    due_date=None,  # Puoi impostare una data di default o parsare dalla email
                    reference_id=email_data['message_id'],
                    reference_type='email',
                )
                
                # Registra l'email importata
                ImportedEmail.objects.create(
                    message_id=email_data['message_id'],
                    subject=email_data['subject'],
                    sender=email_data['from'],
                    received_at=email_data['date'],
                    label=self.email_label,
                    task=task
                )
                
                created_count += 1
            
            # Aggiorna la data dell'ultima importazione
            self.email_label.last_import = timezone.now()
            self.email_label.save()
            
            return len(emails), created_count
            
        except Exception as e:
            logger.exception(f"Errore nell'importazione delle email: {str(e)}")
            raise