import os
import mimetypes
import logging
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from .google_auth import GoogleAuthenticator

logger = logging.getLogger("Utils - Google Drive")

class GoogleDriveUploader:
    """
    Clase para subir archivos a Google Drive
    Compatible con Service Accounts
    """
    
    def __init__(self, authenticator=None, service_account_json=None):
        """
        Inicializa el uploader de Google Drive
        
        Args:
            authenticator (GoogleAuthenticator): Autenticador ya configurado (recomendado)
            service_account_json (str): String con el contenido del JSON de Service Account
        """
        logger.info("Inicializando GoogleDriveUploader")
        if authenticator:
            self.authenticator = authenticator
        else:
            self.authenticator = GoogleAuthenticator(service_account_json)
        
        self.service = None
        self.initialize()
    
    def initialize(self):
        """
        Inicializa el servicio de Google Drive
        """
        try:
            logger.info("Inicializando servicio de Google Drive")
            # Autenticar solo con Drive si no está ya autenticado
            if not self.authenticator.credentials:
                logger.info("Autenticando con alcance 'drive'")
                self.authenticator.authenticate(['drive'])
            
            self.service = self.authenticator.get_drive_service()
            
            print("Google Drive inicializado exitosamente")
            print("Credenciales sin vencimiento")
            logger.info("Google Drive inicializado exitosamente y credenciales sin vencimiento")
                
        except Exception as e:
            logger.error(f"Error al inicializar Google Drive: {e}")
            print(f"Error al inicializar Google Drive: {e}")
            raise
    
    def upload_file(self, file_path, file_name=None, folder_id=None, description=None, make_public=False):
        """
        Sube un archivo a Google Drive
        
        Args:
            file_path (str): Ruta del archivo a subir
            file_name (str): Nombre del archivo en Drive (opcional)
            folder_id (str): ID de la carpeta donde subir (opcional)
            description (str): Descripción del archivo (opcional)
            make_public (bool): Hacer el archivo público (opcional)
        
        Returns:
            dict: Información del archivo subido
        """
        logger.info(f"Preparando para subir archivo: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"El archivo {file_path} no existe")
            raise FileNotFoundError(f"El archivo {file_path} no existe")
        
        if not file_name:
            file_name = os.path.basename(file_path)
        
        # Detectar tipo MIME automáticamente
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Metadatos del archivo
        file_metadata = {
            'name': file_name,
        }
        
        if description:
            file_metadata['description'] = description
        
        # Verificar y configurar carpeta padre
        if folder_id:
            try:
                # Verificar que la carpeta existe
                folder = self.service.files().get(fileId=folder_id, supportsAllDrives=True).execute()
                file_metadata['parents'] = [folder_id]
                logger.info(f"Subiendo a carpeta: {folder.get('name')} ({folder_id})")
                print(f"Subiendo a carpeta: {folder.get('name')} ({folder_id})")
            except HttpError as error:
                if error.resp.status == 404:
                    logger.warning(f"Carpeta no encontrada (ID: {folder_id}), subiendo a la raíz")
                    print(f"Carpeta no encontrada (ID: {folder_id})")
                    print("Subiendo a la carpeta raíz de Drive")
                    folder_id = None
                else:
                    logger.error(f"Error al verificar carpeta: {error}")
                    print(f"Error al verificar carpeta: {error}")
                    raise
        
        # Configurar el tipo de media
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        
        try:
            # Subir el archivo
            file_size = os.path.getsize(file_path)
            logger.info(f"Subiendo: {file_name} ({file_size:,} bytes)")
            print(f"Subiendo: {file_name} ({file_size:,} bytes)")
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,mimeType,createdTime,webViewLink',
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"Archivo subido exitosamente: {file.get('name')} (ID: {file.get('id')})")
            print(f"Archivo subido exitosamente:")
            print(f"   Nombre: {file.get('name')}")
            print(f"   ID: {file.get('id')}")
            print(f"   Tamaño: {file.get('size', 'N/A')} bytes")
            print(f"   Enlace: {file.get('webViewLink')}")
            
            # Hacer público si se solicita
            if make_public:
                logger.info(f"Haciendo público el archivo ID: {file.get('id')}")
                self.make_file_public(file.get('id'))
            
            return file
            
        except HttpError as error:
            logger.error(f"Error al subir archivo: {error}")
            print(f"Error al subir archivo: {error}")
            if 'insufficient permissions' in str(error).lower():
                print("Tip: Asegúrate de compartir la carpeta con la Service Account")
            raise
    
    def make_file_public(self, file_id):
        """
        Hace un archivo público
        
        Args:
            file_id (str): ID del archivo
        """
        try:
            logger.info(f"Configurando archivo como público: {file_id}")
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            print("Archivo configurado como público")
            logger.info(f"Archivo {file_id} configurado como público")
            
        except HttpError as error:
            logger.error(f"Error al hacer archivo público: {error}")
            print(f"Error al hacer archivo público: {error}")
    
    def create_folder(self, folder_name, parent_folder_id=None):
        """
        Crea una carpeta en Google Drive
        
        Args:
            folder_name (str): Nombre de la carpeta
            parent_folder_id (str): ID de la carpeta padre (opcional)
        
        Returns:
            str: ID de la carpeta creada
        """
        logger.info(f"Creando carpeta: {folder_name} (Padre: {parent_folder_id})")
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        # Verificar carpeta padre si se especifica
        if parent_folder_id:
            try:
                # Verificar que la carpeta padre existe
                parent_folder = self.service.files().get(fileId=parent_folder_id).execute()
                file_metadata['parents'] = [parent_folder_id]
                logger.info(f"Creando carpeta '{folder_name}' en: {parent_folder.get('name')}")
                print(f"Creando carpeta '{folder_name}' en: {parent_folder.get('name')}")
            except HttpError as error:
                if error.resp.status == 404:
                    logger.warning(f"Carpeta padre no encontrada (ID: {parent_folder_id}), creando en raíz")
                    print(f"Carpeta padre no encontrada (ID: {parent_folder_id})")
                    print("Creando carpeta en la raíz de Drive")
                elif error.resp.status == 403:
                    logger.warning(f"Sin permisos para acceder a carpeta padre (ID: {parent_folder_id}), creando en raíz")
                    print(f"Sin permisos para acceder a carpeta padre (ID: {parent_folder_id})")
                    print("Creando carpeta en la raíz de Drive")
                else:
                    logger.error(f"Error al verificar carpeta padre: {error}")
                    print(f"Error al verificar carpeta padre: {error}")
                    print("Creando carpeta en la raíz de Drive")
            except Exception as e:
                logger.error(f"Error inesperado al verificar carpeta padre: {e}")
                print(f"Error inesperado al verificar carpeta padre: {e}")
                print("Creando carpeta en la raíz de Drive")
        
        try:
            file = self.service.files().create(
                body=file_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            folder_id = file.get('id')
            logger.info(f"Carpeta creada: {file.get('name')} (ID: {folder_id})")
            print(f"Carpeta creada: {file.get('name')}")
            print(f"   ID: {folder_id}")
            print(f"   Enlace: {file.get('webViewLink')}")
            
            return folder_id
            
        except HttpError as error:
            logger.error(f"Error al crear carpeta: {error}")
            print(f"Error al crear carpeta: {error}")
            if error.resp.status == 403:
                print("Tip: Asegúrate de que la Service Account tenga permisos de escritura")
            raise
    
    def find_folder_by_name(self, folder_name, parent_folder_id=None):
        """
        Busca una carpeta por nombre
        
        Args:
            folder_name (str): Nombre de la carpeta a buscar
            parent_folder_id (str): ID de la carpeta padre donde buscar (opcional)
        
        Returns:
            str: ID de la carpeta encontrada o None si no existe
        """
        logger.info(f"Buscando carpeta por nombre: {folder_name} (Padre: {parent_folder_id})")
        try:
            # Verificar carpeta padre si se especifica
            if parent_folder_id:
                try:
                    # Verificar que la carpeta padre existe
                    parent_folder = self.service.files().get(fileId=parent_folder_id).execute()
                    logger.info(f"Buscando '{folder_name}' en: {parent_folder.get('name')}")
                    print(f"Buscando '{folder_name}' en: {parent_folder.get('name')}")
                except HttpError as error:
                    if error.resp.status == 404:
                        logger.warning(f"Carpeta padre no encontrada (ID: {parent_folder_id}), buscando en toda la unidad")
                        print(f"Carpeta padre no encontrada (ID: {parent_folder_id})")
                        print("Buscando en toda la unidad de Drive")
                        parent_folder_id = None
                    elif error.resp.status == 403:
                        logger.warning(f"Sin permisos para acceder a carpeta padre (ID: {parent_folder_id}), buscando en toda la unidad")
                        print(f"Sin permisos para acceder a carpeta padre (ID: {parent_folder_id})")
                        print("Buscando en toda la unidad de Drive")
                        parent_folder_id = None
                    else:
                        logger.error(f"Error al verificar carpeta padre: {error}")
                        print(f"Error al verificar carpeta padre: {error}")
                        print("Buscando en toda la unidad de Drive")
                        parent_folder_id = None
                except Exception as e:
                    logger.error(f"Error inesperado al verificar carpeta padre: {e}")
                    print(f"Error inesperado al verificar carpeta padre: {e}")
                    print("Buscando en toda la unidad de Drive")
                    parent_folder_id = None
            
            # Construir query
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                fields="files(id,name)"
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                logger.info(f"Carpeta encontrada: {folder_name} (ID: {folder_id})")
                print(f"Carpeta encontrada: {folder_name} (ID: {folder_id})")
                return folder_id
            else:
                logger.info(f"Carpeta no encontrada: {folder_name}")
                print(f"Carpeta no encontrada: {folder_name}")
                return None
                
        except HttpError as error:
            logger.error(f"Error al buscar carpeta: {error}")
            print(f"Error al buscar carpeta: {error}")
            if error.resp.status == 403:
                print("Tip: Asegúrate de que la Service Account tenga permisos de lectura")
            return None
    
    def get_or_create_folder(self, folder_name, parent_folder_id=None):
        """
        Obtiene el ID de una carpeta o la crea si no existe
        
        Args:
            folder_name (str): Nombre de la carpeta
            parent_folder_id (str): ID de la carpeta padre (opcional)
        
        Returns:
            str: ID de la carpeta
        """
        logger.info(f"Obteniendo o creando carpeta: {folder_name} (Padre: {parent_folder_id})")
        # Buscar carpeta existente
        folder_id = self.find_folder_by_name(folder_name, parent_folder_id)
        
        if folder_id:
            logger.info(f"Carpeta ya existe: {folder_id}")
            return folder_id
        
        # Crear carpeta si no existe
        logger.info(f"Creando nueva carpeta: {folder_name}")
        print(f"Creando nueva carpeta: {folder_name}")
        return self.create_folder(folder_name, parent_folder_id)
    
    def upload_to_folder_by_name(self, file_path, folder_name, file_name=None, create_if_not_exists=True):
        """
        Sube un archivo a una carpeta especificada por nombre
        
        Args:
            file_path (str): Ruta del archivo a subir
            folder_name (str): Nombre de la carpeta donde subir
            file_name (str): Nombre del archivo en Drive (opcional)
            create_if_not_exists (bool): Crear carpeta si no existe
        
        Returns:
            dict: Información del archivo subido
        """
        logger.info(f"Subiendo archivo {file_path} a carpeta {folder_name} (create_if_not_exists={create_if_not_exists})")
        if create_if_not_exists:
            folder_id = self.get_or_create_folder(folder_name)
        else:
            folder_id = self.find_folder_by_name(folder_name)
            if not folder_id:
                logger.error(f"Carpeta no encontrada: {folder_name}")
                raise FileNotFoundError(f"Carpeta no encontrada: {folder_name}")
        
        return self.upload_file(file_path, file_name, folder_id)
    
    def upload_multiple_files(self, file_paths, folder_id=None, progress_callback=None):
        """
        Sube múltiples archivos a Google Drive
        
        Args:
            file_paths (list): Lista de rutas de archivos a subir
            folder_id (str): ID de la carpeta donde subir (opcional)
            progress_callback (function): Función callback para progreso (opcional)
        
        Returns:
            list: Lista de información de archivos subidos
        """
        logger.info(f"Subiendo múltiples archivos: {file_paths} a carpeta {folder_id}")
        uploaded_files = []
        total_files = len(file_paths)
        
        print(f"Subiendo {total_files} archivos...")
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                logger.info(f"[{i}/{total_files}] Procesando: {os.path.basename(file_path)}")
                print(f"\n[{i}/{total_files}] Procesando: {os.path.basename(file_path)}")
                
                file_info = self.upload_file(file_path, folder_id=folder_id)
                uploaded_files.append(file_info)
                
                if progress_callback:
                    progress_callback(i, total_files, file_info)
                    
            except Exception as e:
                logger.error(f"Error al subir {file_path}: {e}")
                print(f"Error al subir {file_path}: {e}")
        
        logger.info(f"Subida completada: {len(uploaded_files)}/{total_files} archivos exitosos")
        print(f"\nSubida completada: {len(uploaded_files)}/{total_files} archivos exitosos")
        return uploaded_files
    
    def upload_folder_structure(self, local_folder_path, drive_folder_name=None, parent_folder_id=None):
        """
        Sube una carpeta completa manteniendo la estructura
        
        Args:
            local_folder_path (str): Ruta de la carpeta local
            drive_folder_name (str): Nombre de la carpeta en Drive (opcional)
            parent_folder_id (str): ID de carpeta padre en Drive (opcional)
        
        Returns:
            dict: Información de la subida
        """
        from pathlib import Path
        
        logger.info(f"Subiendo estructura de carpeta: {local_folder_path} a Drive (nombre en Drive: {drive_folder_name}, padre: {parent_folder_id})")
        local_path = Path(local_folder_path)
        
        if not local_path.exists() or not local_path.is_dir():
            logger.error(f"La carpeta {local_folder_path} no existe")
            raise ValueError(f"La carpeta {local_folder_path} no existe")
        
        if not drive_folder_name:
            drive_folder_name = local_path.name
        
        # Crear carpeta principal en Drive
        main_folder_id = self.create_folder(drive_folder_name, parent_folder_id)
        
        uploaded_files = []
        created_folders = {str(local_path): main_folder_id}
        
        # Recorrer todos los archivos y carpetas
        for item_path in local_path.rglob('*'):
            if item_path.is_file():
                # Determinar carpeta padre en Drive
                relative_parent = item_path.parent.relative_to(local_path)
                
                if str(relative_parent) == '.':
                    # Archivo en carpeta raíz
                    target_folder_id = main_folder_id
                else:
                    # Crear estructura de carpetas si es necesario
                    parent_parts = relative_parent.parts
                    current_parent_id = main_folder_id
                    
                    for part in parent_parts:
                        folder_key = str(local_path / relative_parent.parents[len(parent_parts)-1-parent_parts[::-1].index(part)])
                        
                        if folder_key not in created_folders:
                            logger.info(f"Creando subcarpeta: {part} en {current_parent_id}")
                            current_parent_id = self.create_folder(part, current_parent_id)
                            created_folders[folder_key] = current_parent_id
                        else:
                            current_parent_id = created_folders[folder_key]
                    
                    target_folder_id = current_parent_id
                
                # Subir archivo
                try:
                    logger.info(f"Subiendo archivo: {item_path} a carpeta {target_folder_id}")
                    file_info = self.upload_file(str(item_path), folder_id=target_folder_id)
                    uploaded_files.append(file_info)
                except Exception as e:
                    logger.error(f"Error al subir {item_path}: {e}")
                    print(f"Error al subir {item_path}: {e}")
        
        result = {
            'main_folder_id': main_folder_id,
            'uploaded_files': uploaded_files,
            'total_files': len(uploaded_files),
            'created_folders': len(created_folders)
        }
        
        logger.info(f"Estructura subida: {len(uploaded_files)} archivos, {len(created_folders)} carpetas")
        print(f"Estructura subida: {len(uploaded_files)} archivos, {len(created_folders)} carpetas")
        return result
    
    def get_authenticator(self):
        """
        Obtiene el objeto authenticator para usar con otros servicios
        
        Returns:
            GoogleAuthenticator: Objeto authenticator
        """
        logger.info("Obteniendo objeto authenticator")
        return self.authenticator
    
    def verify_folder_access(self, folder_id, verbose=True):
        """
        Verifica si se puede acceder a una carpeta específica
        
        Args:
            folder_id (str): ID de la carpeta a verificar
            verbose (bool): Mostrar información detallada
            
        Returns:
            dict: Información sobre el acceso a la carpeta
        """
        logger.info(f"Verificando acceso a carpeta: {folder_id}")
        result = {
            'exists': False,
            'accessible': False,
            'name': None,
            'id': folder_id,
            'error': None
        }
        
        try:
            folder = self.service.files().get(fileId=folder_id).execute()
            result['exists'] = True
            result['accessible'] = True
            result['name'] = folder.get('name')
            
            if verbose:
                logger.info(f"Carpeta accesible: {folder_id} ({folder.get('name')})")
                print(f"Carpeta accesible:")
                print(f"   ID: {folder_id}")
                print(f"   Nombre: {folder.get('name')}")
                print(f"   Enlace: {folder.get('webViewLink', 'N/A')}") 
                
        except HttpError as error:
            result['error'] = str(error)
            if error.resp.status == 404:
                result['exists'] = False
                logger.warning(f"Carpeta no encontrada (ID: {folder_id})")
                if verbose:
                    print(f"Carpeta no encontrada (ID: {folder_id})")
                    print(" + Posibles causas:")
                    print("   - La carpeta fue eliminada")
                    print("   - El ID de carpeta es incorrecto")
            elif error.resp.status == 403:
                result['exists'] = True  # Existe pero no tenemos permisos
                result['accessible'] = False
                logger.warning(f"Sin permisos para acceder a carpeta (ID: {folder_id})")
                if verbose:
                    print(f"Sin permisos para acceder a carpeta (ID: {folder_id})")
                    print(" + Posibles soluciones:")
                    print("   - Compartir la carpeta con la Service Account")
                    print("   - Verificar los permisos de la Service Account")
            else:
                logger.error(f"Error al verificar carpeta: {error}")
                if verbose:
                    print(f"❌ Error al verificar carpeta: {error}")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error inesperado al verificar carpeta: {e}")
            if verbose:
                print(f"❌ Error inesperado: {e}")
        
        return result
    
    def list_files(self, folder_id=None, max_results=10, show_details=True):
        """
        Lista archivos en Google Drive
        
        Args:
            folder_id (str): ID de la carpeta a listar (opcional)
            max_results (int): Número máximo de archivos a mostrar
            show_details (bool): Mostrar detalles de archivos
        
        Returns:
            list: Lista de archivos
        """
        logger.info(f"Listando archivos en carpeta: {folder_id} (max_results={max_results})")
        try:
            query = ""
            if folder_id:
                query = f"'{folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, size, mimeType, createdTime, owners)",
                orderBy="createdTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                logger.info("No se encontraron archivos")
                print("No se encontraron archivos")
                return []
            
            logger.info(f"Archivos encontrados ({len(files)}):")
            print(f"Archivos encontrados ({len(files)}):")
            
            if show_details:
                for file in files:
                    size = file.get('size', 'N/A')
                    if size != 'N/A':
                        size = f"{int(size):,} bytes"
                    
                    file_type = "Carpeta" if file.get('mimeType') == 'application/vnd.google-apps.folder' else "Archivo"
                    logger.info(f"{file_type} {file['name']} (ID: {file['id']}) Tamaño: {size}")
                    print(f"   {file_type} {file['name']}")
                    print(f"       ID: {file['id']}")
                    print(f"       Tamaño: {size}")
                    print()
            else:
                for file in files:
                    file_type = "Carpeta" if file.get('mimeType') == 'application/vnd.google-apps.folder' else "Archivo"
                    logger.info(f"{file_type} {file['name']} (ID: {file['id']})")
                    print(f"   {file_type} {file['name']} (ID: {file['id']})")
            
            return files
            
        except HttpError as error:
            logger.error(f"Error al listar archivos: {error}")
            print(f"Error al listar archivos: {error}")
            raise