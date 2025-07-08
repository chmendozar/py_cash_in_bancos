import os
import base64
import mimetypes
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.errors import HttpError
from .google_auth import GoogleAuthenticator
import logging

logger = logging.getLogger("Utils - Gmail Sender")

class GmailSender:
    """
    Clase para envío de emails usando Gmail API
    Compatible con Service Accounts
    """
    
    def __init__(self, authenticator=None, service_account_json=None):
        """
        Inicializa el enviador de Gmail
        
        Args:
            authenticator (GoogleAuthenticator): Autenticador ya configurado (recomendado)
            service_account_json (str): String con el contenido del JSON de Service Account
        """
        if authenticator:
            self.authenticator = authenticator
            logger.info("Usando autenticador proporcionado para GmailSender")
        else:
            self.authenticator = GoogleAuthenticator(service_account_json)
            logger.info("Inicializando GoogleAuthenticator con JSON proporcionado")
        
        self.service = None
        self.user_email = None
        self.initialize()
    
    def initialize(self):
        """
        Inicializa el servicio de Gmail
        """
        try:
            # Autenticar solo con Gmail si no está ya autenticado
            if not self.authenticator.is_authenticated():
                logger.info("Autenticando con alcance 'gmail'")
                self.authenticator.authenticate(['gmail'])
            
            self.service = self.authenticator.get_gmail_service()
            logger.info("Servicio de Gmail inicializado correctamente")
            
            # Obtener información del usuario
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile.get('emailAddress')
            logger.info(f"Gmail inicializado para: {self.user_email}")
            
            # Mostrar información del tipo de autenticación
            auth_info = self.authenticator.get_auth_info()
            print(f"Gmail inicializado para: {self.user_email}")
            print(f"Tipo de autenticación: {auth_info['tipo']}")
            if auth_info['sin_vencimiento']:
                print("Credenciales sin vencimiento")
                logger.info("Credenciales sin vencimiento")
            
        except Exception as e:
            logger.error(f"Error al inicializar Gmail: {e}")
            print(f"Error al inicializar Gmail: {e}")
            raise
    
    def create_message(self, to, subject, body, cc=None, bcc=None, attachments=None, body_type='plain'):
        """
        Crea un mensaje de email
        
        Args:
            to (str or list): Destinatario(s)
            subject (str): Asunto del email
            body (str): Cuerpo del email
            cc (str or list): Destinatarios en copia (opcional)
            bcc (str or list): Destinatarios en copia oculta (opcional)
            attachments (list): Lista de rutas de archivos adjuntos (opcional)
            body_type (str): Tipo de cuerpo ('plain' o 'html')
        
        Returns:
            dict: Mensaje codificado en base64
        """
        logger.debug(f"Creando mensaje para: {to}, asunto: {subject}, adjuntos: {attachments}")
        # Crear mensaje
        message = MIMEMultipart()
        
        # Configurar destinatarios
        if isinstance(to, list):
            message['to'] = ', '.join(to)
        else:
            message['to'] = to
        
        if cc:
            if isinstance(cc, list):
                message['cc'] = ', '.join(cc)
            else:
                message['cc'] = cc
        
        if bcc:
            if isinstance(bcc, list):
                message['bcc'] = ', '.join(bcc)
            else:
                message['bcc'] = bcc
        
        message['subject'] = subject
        message['from'] = self.user_email
        
        # Agregar cuerpo del mensaje
        if body_type.lower() == 'html':
            message.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            message.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Agregar archivos adjuntos
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    self._add_attachment(message, file_path)
                else:
                    logger.warning(f"Archivo adjunto no encontrado: {file_path}")
                    print(f"Advertencia: Archivo no encontrado: {file_path}")
        
        # Codificar mensaje
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        logger.debug("Mensaje creado y codificado en base64")
        return {'raw': raw_message}
    
    def _add_attachment(self, message, file_path):
        """
        Agrega un archivo adjunto al mensaje
        
        Args:
            message (MIMEMultipart): Mensaje al que agregar el adjunto
            file_path (str): Ruta del archivo a adjuntar
        """
        try:
            # Obtener tipo MIME
            content_type, encoding = mimetypes.guess_type(file_path)
            
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            
            main_type, sub_type = content_type.split('/', 1)
            
            # Leer archivo
            with open(file_path, 'rb') as f:
                attachment_data = f.read()
            
            # Crear adjunto
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(attachment_data)
            encoders.encode_base64(attachment)
            
            # Configurar headers
            filename = os.path.basename(file_path)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            
            message.attach(attachment)
            logger.info(f"Adjunto agregado: {filename}")
            print(f"Adjunto agregado: {filename}")
            
        except Exception as e:
            logger.error(f"Error al agregar adjunto {file_path}: {e}")
            print(f"Error al agregar adjunto {file_path}: {e}")
    
    def send_message(self, to, subject, body, cc=None, bcc=None, attachments=None, body_type='plain'):
        """
        Envía un email
        
        Args:
            to (str or list): Destinatario(s)
            subject (str): Asunto del email
            body (str): Cuerpo del email
            cc (str or list): Destinatarios en copia (opcional)
            bcc (str or list): Destinatarios en copia oculta (opcional)
            attachments (list): Lista de rutas de archivos adjuntos (opcional)
            body_type (str): Tipo de cuerpo ('plain' o 'html')
        
        Returns:
            dict: Información del mensaje enviado
        """
        try:
            # Crear mensaje
            message = self.create_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                body_type=body_type
            )
            
            # Enviar mensaje
            logger.info(f"Enviando email a: {to} | Asunto: {subject}")
            print(f"Enviando email a: {to}")
            print(f"Asunto: {subject}")
            
            result = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            logger.info(f"Email enviado exitosamente. ID: {result['id']}")
            print(f"Email enviado exitosamente. ID: {result['id']}")
            return result
            
        except HttpError as error:
            logger.error(f"Error al enviar email: {error}")
            print(f"Error al enviar email: {error}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al enviar email: {e}")
            print(f"Error inesperado al enviar email: {e}")
            raise
    
    def send_html_email(self, to, subject, html_body, cc=None, bcc=None, attachments=None):
        """
        Envía un email con formato HTML
        
        Args:
            to (str or list): Destinatario(s)
            subject (str): Asunto del email
            html_body (str): Cuerpo del email en HTML
            cc (str or list): Destinatarios en copia (opcional)
            bcc (str or list): Destinatarios en copia oculta (opcional)
            attachments (list): Lista de rutas de archivos adjuntos (opcional)
        
        Returns:
            dict: Información del mensaje enviado
        """
        logger.debug(f"Enviando email HTML a: {to} | Asunto: {subject}")
        return self.send_message(
            to=to,
            subject=subject,
            body=html_body,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            body_type='html'
        )
    
    def send_template_email(self, to, subject, template_data, cc=None, bcc=None, attachments=None):
        """
        Envía un email usando un template HTML básico
        
        Args:
            to (str or list): Destinatario(s)
            subject (str): Asunto del email
            template_data (dict): Datos para el template (title, content, footer)
            cc (str or list): Destinatarios en copia (opcional)
            bcc (str or list): Destinatarios en copia oculta (opcional)
            attachments (list): Lista de rutas de archivos adjuntos (opcional)
        
        Returns:
            dict: Información del mensaje enviado
        """
        # Template HTML básico
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #f4f4f4;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px;
                }}
                .content {{
                    padding: 20px;
                    background-color: #fff;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                {footer}
            </div>
        </body>
        </html>
        """
        
        # Formatear template
        html_body = html_template.format(
            title=template_data.get('title', 'Notificación'),
            content=template_data.get('content', ''),
            footer=template_data.get('footer', 'Enviado automáticamente')
        )
        logger.debug(f"Enviando email con template a: {to} | Asunto: {subject}")
        return self.send_html_email(
            to=to,
            subject=subject,
            html_body=html_body,
            cc=cc,
            bcc=bcc,
            attachments=attachments
        )
    
    def send_multiple_emails(self, email_list):
        """
        Envía múltiples emails
        
        Args:
            email_list (list): Lista de diccionarios con datos de email
                              Cada diccionario debe tener: to, subject, body
                              Opcionales: cc, bcc, attachments, body_type
        
        Returns:
            list: Lista de resultados de envío
        """
        results = []
        
        for email_data in email_list:
            try:
                logger.info(f"Enviando email múltiple a: {email_data['to']} | Asunto: {email_data['subject']}")
                result = self.send_message(
                    to=email_data['to'],
                    subject=email_data['subject'],
                    body=email_data['body'],
                    cc=email_data.get('cc'),
                    bcc=email_data.get('bcc'),
                    attachments=email_data.get('attachments'),
                    body_type=email_data.get('body_type', 'plain')
                )
                results.append({
                    'status': 'success',
                    'to': email_data['to'],
                    'message_id': result['id']
                })
            except Exception as e:
                logger.error(f"Error al enviar email a {email_data['to']}: {e}")
                results.append({
                    'status': 'error',
                    'to': email_data['to'],
                    'error': str(e)
                })
        
        logger.info(f"Envío múltiple completado. Total: {len(results)}")
        return results
    
    def get_user_info(self):
        """
        Obtiene información del usuario autenticado
        
        Returns:
            dict: Información del perfil del usuario
        """
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            logger.info(f"Información de usuario obtenida para: {profile.get('emailAddress')}")
            return {
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal'),
                'history_id': profile.get('historyId')
            }
        except HttpError as error:
            logger.error(f"Error al obtener información del usuario: {error}")
            print(f"Error al obtener información del usuario: {error}")
            return None 