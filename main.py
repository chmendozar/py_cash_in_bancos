import logging
from datetime import datetime
import traceback
import platform
import os
import psutil
import variables_globales as vg
from utilidades.limpieza import cerrarProcesos as Limpieza
from modulos.bot_00_configuracion import bot_run as Bot_00_Configuracion
from modulos.bot_01_ci_bcp import bot_run as Bot_01_CI_BCP
from modulos.bot_02_bbva_ci_soles import bot_run as Bot_02_CI_BBVA_SOLES
from modulos.bot_03_bbva_ci_dolares import bot_run as Bot_03_CI_BBVA_DOLARES
from utilidades.notificaiones_whook import WebhookNotifier

logger = logging.getLogger("Main - Orquestador")

def obtener_info_sistema():
    """
    Recopila información del sistema para diagnóstico.

    Returns:
        dict: Información básica del sistema
    """
    try:
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "memory": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
            "cpu_count": os.cpu_count(),
            "cpu_usage": f"{psutil.cpu_percent()}%",
            "available_memory": f"{round(psutil.virtual_memory().available / (1024**3), 2)} GB"
        }
        return info
    except Exception as e:
        logger.warning(f"No se pudo obtener información completa del sistema: {e}")
        return {"error": str(e)}

def main():
    inicio = datetime.now()
    
    # Limpieza de ambiente
    # Definir lista de procesos a cerrar según el sistema operativo
    if platform.system() == "Windows":
        lista_procesos = ["chrome.exe", "chromedriver.exe", "excel.exe"]
    elif platform.system() == "Darwin":  # macOS
        lista_procesos = ["Google Chrome", "chromedriver", "Microsoft Excel"]
    elif platform.system() == "Linux":
        lista_procesos = ["chrome", "chromedriver", "excel"]
    else:
        lista_procesos = []
    Limpieza(lista_procesos)

    logger.info(f"==================== INICIO DE ORQUESTACIÓN ====================")
    logger.info(f"Inicio de orquestación - {inicio.strftime('%Y-%m-%d %H:%M:%S')}")

    # Recopilar información del sistema
    info_sistema = obtener_info_sistema()
    logger.info(f"Información del sistema: {info_sistema}")

    try:
        # Configuración del bot
        logger.info("Cargando configuración del sistema...")
        cfg = Bot_00_Configuracion()
        if not cfg:
            logger.error("Error al cargar la configuración. Abortando proceso.")
            vg.system_exception = True
            return

        logger.info(f"Configuración cargada exitosamente. Secciones disponibles: {', '.join(cfg.keys())}")

        # Inicializar notificador webhook
        webhook = WebhookNotifier(cfg['webhook']['webhook_rpa_url'])
        webhook.send_notification("Iniciando proceso de orquestación de bots")

        # Ejecución de los bots
        mensaje = ""  # Initialize mensaje variable
        for bot_name, bot_function in [
            ("Bot 01 - BCP", Bot_01_CI_BCP),
            ("Bot 02 - BBVA Soles", Bot_02_CI_BBVA_SOLES),
            ("Bot 03 - BBVA Dólares", Bot_03_CI_BBVA_DOLARES),
            
        ]:
            logger.info(f"==================== INICIANDO {bot_name} ====================")
            webhook.send_notification(f"Iniciando {bot_name}")
            resultado, mensaje = bot_function(cfg, mensaje)
            logger.info(f"{bot_name} completado exitosamente")
            webhook.send_notification(f"{bot_name} completado exitosamente")
            if not resultado:
                logger.error(f"{bot_name} completado con errores: {mensaje}")
                webhook.send_notification(f"{bot_name} completado con errores: {mensaje}")

    except Exception as e:
        error_msg = f"Error en main: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        webhook.send_notification(error_msg)

    finally:
        # Calcular tiempo total de ejecución
        fin = datetime.now()
        tiempo_total = fin - inicio
        logger.info(f"==================== FIN DE ORQUESTACIÓN ====================")
        logger.info(f"Fin de orquestación - {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Tiempo total de ejecución: {tiempo_total}")
        logger.info("Fin del proceso ...")
        webhook.send_notification(f"Proceso finalizado. Tiempo total: {tiempo_total}")

if __name__ == "__main__":
    main()