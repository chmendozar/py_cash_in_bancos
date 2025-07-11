import logging
from pathlib import Path
from config.config import cargar_configuracion
from utilidades.logger import init_logger
from utilidades.limpieza import limpiar_archivos_en_carpeta
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Configuracion del logger
logger = logging.getLogger("Bot 00 - Configurador")

def bot_run():

    try:
        # Funcion para cargar el archivo de configuración
        cfg = cargar_configuracion()
        # Agregar variables de entorno al diccionario de configuración
        cfg['env_vars'] = {
            'bcp': {
                'tarjeta': os.getenv('BCP_TARJETA'),
                'password': os.getenv('BCP_PASSWORD')
            },
            'bbva': {
                'code': os.getenv('BBVA_CODE'), 
                'user': os.getenv('BBVA_USER'),
                'password': os.getenv('BBVA_PASSWORD')
            },
            'gcp': {
                'service_account_json': os.getenv('SERVICE_GCP_JSON'),
                'folder_id': os.getenv('GCP_FOLDER_ID')
            },
            'anticaptcha': {
                'api_key': os.getenv('ANTICAPTCHA_API_KEY')
            },
            'bcp_cuenta': os.getenv('BCP_CUENTA'),
            'webhook_rpa_url': os.getenv('WEBHOOK_RPA_URL')
        }
        # Se crea la carpeta de logs si no existe
        if not Path(cfg["rutas"]["ruta_log"]).exists():
            Path(cfg["rutas"]["ruta_log"]).mkdir(parents=True)

        # Se crea la carpeta de input si no existe
        ruta_input = Path(cfg["rutas"]["ruta_input"])
        if not ruta_input.exists():
            ruta_input.mkdir(parents=True)
        else:
            # Eliminar todas las subcarpetas dentro de ruta_input
            limpiar_archivos_en_carpeta(ruta_input)

        # Se crea la carpeta de output si no existe
        if not Path(cfg["rutas"]["ruta_output"]).exists():
            Path(cfg["rutas"]["ruta_output"]).mkdir(parents=True)

        # Inicializar logger
        init_logger(ruta_log=cfg["archivos"]["archivos_log"], nivel=logging.INFO)
        logger.info("Inicio del proceso ...")

        # Imprimir configuracion
        logger.info(f"Configuracion cargada")
        logger.info(f"Ruta de logs: {cfg['rutas']['ruta_log']}")
        logger.info(f"Ruta de input: {cfg['rutas']['ruta_input']}")
        logger.info(f"Ruta de output: {cfg['rutas']['ruta_output']}")
        logger.info(f"Achivo de logs: {cfg['archivos']['archivos_log']}")

        return cfg
    
    except Exception as e:
        logger.error(f"Error en bot_run: {e}")
        return None
    finally:
        logger.info("Fin del proceso ...")