"""
Paquete de utilidades para el bot de Cash-In
"""

# Importar clases principales para facilitar su uso
try:
    from .google_auth import GoogleAuthenticator
    from .gmail_sender import GmailSender
    from .google_drive import GoogleDriveUploader
    from .logger import Logger
    from .excepciones import *
    
    # Versión del paquete
    __version__ = "1.0.0"
    
    # Clases disponibles para importación
    __all__ = [
        'GoogleAuthenticator',
        'GmailSender', 
        'GoogleDriveUploader',
        'Logger'
    ]
    
except ImportError as e:
    # Si alguna importación falla, mostrar advertencia pero no interrumpir
    print(f"Advertencia: No se pudo importar alguna clase: {e}")
    
    # Definir solo las clases que se importaron exitosamente
    __all__ = [] 