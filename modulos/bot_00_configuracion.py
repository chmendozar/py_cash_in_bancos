import logging
from pathlib import Path
from config.config import cargar_configuracion
from utilidades.logger import init_logger

# Configuracion del logger
logger = logging.getLogger("Bot 00 - Configurador")

def bot_run():

    try:
        # Funcion para cargar el archivo de configuración
        cfg = cargar_configuracion()

        # Se crea la carpeta de logs si no existe
        if not Path(cfg["rutas"]["ruta_log"]).exists():
            Path(cfg["rutas"]["ruta_log"]).mkdir(parents=True)

        # Se crea la carpeta de input si no existe
        ruta_input = Path(cfg["rutas"]["ruta_input"])
        if not ruta_input.exists():
            ruta_input.mkdir(parents=True)
        else:
            pass
            # # Limpiar el directorio ruta_input
            # for archivo in ruta_input.iterdir():
            #     try:
            #         if archivo.is_file():
            #             archivo.unlink()
            #         elif archivo.is_dir():
            #             # Si hay subdirectorios, los elimina recursivamente
            #             import shutil
            #             shutil.rmtree(archivo)
            #     except Exception as e:
            #         logger.warning(f"No se pudo eliminar {archivo}: {e}")

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