import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
    
    def __init__(self, service_account_file='config/service_account.json', impersonate_user=None):
        """
        Inicializa el autenticador
        
        Args:
            service_account_file (str): Ruta al archivo de Service Account JSON
            impersonate_user (str): Email del usuario a impersonar (opcional, para Google Workspace)
        """
        self.service_account_file = service_account_file
        self.impersonate_user = impersonate_user
        self.credentials = None
        self.services = {}
        self.service_account_info = None
    
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
        return list(dict.fromkeys(combined_scopes))
    
    def load_service_account_info(self):
        """
        Carga información del archivo de Service Account
        """
        try:
            with open(self.service_account_file, 'r') as f:
                self.service_account_info = json.load(f)
            return True
        except Exception as e:
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
        
        if not os.path.exists(self.service_account_file):
            raise FileNotFoundError(f"Archivo de Service Account no encontrado: {self.service_account_file}")
        
        try:
            # Cargar información del Service Account
            if not self.load_service_account_info():
                raise ValueError("No se pudo cargar información del Service Account")
            
            # Cargar credenciales de Service Account
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=scopes)
            
            # Si se especifica un usuario para impersonar (Google Workspace)
            if self.impersonate_user:
                self.credentials = self.credentials.with_subject(self.impersonate_user)
                print(f"Impersonando usuario: {self.impersonate_user}")
            
            print("Autenticación con Service Account exitosa")
            self.show_auth_info()
            return self.credentials
        
        except Exception as e:
            print(f"Error al autenticar con Service Account: {e}")
            raise
    
    def show_auth_info(self):
        """
        Muestra información detallada de la autenticación
        """
        if not self.service_account_info:
            return
        
        print("\nInformación de Service Account:")
        print(f"   Email: {self.service_account_info.get('client_email', 'N/A')}")
        print(f"   Proyecto: {self.service_account_info.get('project_id', 'N/A')}")
        print(f"   Client ID: {self.service_account_info.get('client_id', 'N/A')}")
        print(f"   Tipo: {self.service_account_info.get('type', 'N/A')}")
        
        if self.impersonate_user:
            print(f"   Impersonando: {self.impersonate_user}")
        
        print("   Sin vencimiento de credenciales")
        print("   Ideal para automatizaciones")
        print()
    
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
                print(f"Servicio {service_name} v{api_version} inicializado")
            except HttpError as error:
                print(f"Error al inicializar servicio {service_name}: {error}")
                raise
        
        return self.services[service_key]
    
    def get_gmail_service(self):
        """
        Obtiene el servicio de Gmail
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Gmail
        """
        return self.get_service('gmail', 'v1')
    
    def get_drive_service(self):
        """
        Obtiene el servicio de Drive
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Drive
        """
        return self.get_service('drive', 'v3')
    
    def get_sheets_service(self):
        """
        Obtiene el servicio de Sheets
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Sheets
        """
        return self.get_service('sheets', 'v4')
    
    def get_calendar_service(self):
        """
        Obtiene el servicio de Calendar
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Calendar
        """
        return self.get_service('calendar', 'v3')