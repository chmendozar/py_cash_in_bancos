import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger("Utils - Google Auth")

class GoogleAuthenticator:
    """
    Clase para manejar la autenticación con múltiples servicios de Google
    usando Service Account
    """
    
    # Scopes para diferentes servicios
    SCOPES = {
        'gmail': [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.readonly'
        ],
        'drive': [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive'
        ],
        'sheets': [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/spreadsheets.readonly'
        ],
        'calendar': [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.readonly'
        ]
    }
    
    def __init__(self, service_account_json=None, impersonate_user=None):
        """
        Inicializa el autenticador
        
        Args:
            service_account_json (str): String con el contenido del JSON de Service Account
            impersonate_user (str): Email del usuario a impersonar (opcional, para Google Workspace)
        """
        self.service_account_json = service_account_json
        self.impersonate_user = impersonate_user
        self.credentials = None
        self.services = {}
        self.service_account_info = None
        logger.debug(f"Inicializando GoogleAuthenticator con JSON de Service Account y usuario a impersonar: {impersonate_user}")
    
    def get_combined_scopes(self, services=None):
        """
        Obtiene los scopes combinados para los servicios especificados
        
        Args:
            services (list): Lista de servicios ('gmail', 'drive', 'sheets', 'calendar')
        
        Returns:
            list: Lista de scopes combinados
        """
        if services is None:
            services = ['gmail', 'drive']
        
        combined_scopes = []
        for service in services:
            if service in self.SCOPES:
                combined_scopes.extend(self.SCOPES[service])
        
        # Remover duplicados manteniendo el orden
        logger.debug(f"Scopes combinados para servicios {services}: {combined_scopes}")
        return list(dict.fromkeys(combined_scopes))
    
    def load_service_account_info(self):
        """
        Carga información del archivo de Service Account
        """
        try:
            self.service_account_json = self.service_account_json.replace('\\"', '"')
            self.service_account_info = json.loads(self.service_account_json)
            logger.info("Información de Service Account cargada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al cargar información de Service Account: {e}")
            print(f"Error al cargar información de Service Account: {e}")
            return False
    
    def authenticate(self, services=None):
        """
        Autentica usando Service Account
        
        Args:
            services (list): Lista de servicios a autenticar ('gmail', 'drive', etc.)
        
        Returns:
            service_account.Credentials: Credenciales de Service Account
        """
        if services is None:
            services = ['gmail', 'drive']
        
        scopes = self.get_combined_scopes(services)
        
        try:
            # Cargar información del Service Account
            if not self.load_service_account_info():
                logger.error("No se pudo cargar información del Service Account")
                raise ValueError("No se pudo cargar información del Service Account")
            
            # Cargar credenciales de Service Account
            self.credentials = service_account.Credentials.from_service_account_info(
                self.service_account_info, scopes=scopes)
            logger.info(f"Credenciales de Service Account cargadas para scopes: {scopes}")
            
            # Si se especifica un usuario para impersonar (Google Workspace)
            if self.impersonate_user:
                self.credentials = self.credentials.with_subject(self.impersonate_user)
                logger.info(f"Impersonando usuario: {self.impersonate_user}")
                print(f"Impersonando usuario: {self.impersonate_user}")
            
            logger.info("Autenticación con Service Account exitosa")
            print("Autenticación con Service Account exitosa")
            return self.credentials
        
        except Exception as e:
            logger.exception(f"Error al autenticar con Service Account: {e}")
            print(f"Error al autenticar con Service Account: {e}")
            raise
    

    
    def get_service(self, service_name, version='v1'):
        """
        Obtiene un servicio de Google API
        
        Args:
            service_name (str): Nombre del servicio ('gmail', 'drive', 'sheets', 'calendar')
            version (str): Versión de la API
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Google API
        """
        if not self.credentials:
            logger.error("No hay credenciales. Ejecute authenticate() primero.")
            raise ValueError("No hay credenciales. Ejecute authenticate() primero.")
        
        service_key = f"{service_name}_{version}"
        
        if service_key not in self.services:
            try:
                # Versiones específicas para cada servicio
                versions = {
                    'gmail': 'v1',
                    'drive': 'v3',
                    'sheets': 'v4',
                    'calendar': 'v3'
                }
                
                api_version = versions.get(service_name, version)
                
                self.services[service_key] = build(
                    service_name, api_version, credentials=self.credentials)
                logger.info(f"Servicio {service_name} v{api_version} inicializado")
                print(f"Servicio {service_name} v{api_version} inicializado")
            except HttpError as error:
                logger.error(f"Error al inicializar servicio {service_name}: {error}")
                print(f"Error al inicializar servicio {service_name}: {error}")
                raise
        
        return self.services[service_key]
    
    def get_gmail_service(self):
        """
        Obtiene el servicio de Gmail
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Gmail
        """
        logger.debug("Obteniendo servicio de Gmail")
        return self.get_service('gmail', 'v1')
    
    def get_drive_service(self):
        """
        Obtiene el servicio de Drive
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Drive
        """
        logger.debug("Obteniendo servicio de Drive")
        return self.get_service('drive', 'v3')
    
    def get_sheets_service(self):
        """
        Obtiene el servicio de Sheets
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Sheets
        """
        logger.debug("Obteniendo servicio de Sheets")
        return self.get_service('sheets', 'v4')
    
    def get_calendar_service(self):
        """
        Obtiene el servicio de Calendar
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Calendar
        """
        logger.debug("Obteniendo servicio de Calendar")
        return self.get_service('calendar', 'v3')