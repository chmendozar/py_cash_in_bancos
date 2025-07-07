import psutil
import logging
import os

# Configuración del logger
logger = logging.getLogger("Utils - Limpieza Ambiente")

def cerrarProcesos(lista_procesos):
    """
    Cierra los procesos según los nombres proporcionados en la lista, forzando el cierre si es necesario.

    :param lista_procesos: Lista de nombres de procesos a cerrar (ej. ["chrome.exe", "excel.exe"]).
    """
    try:
        logger.info("Inicio del proceso ...")

        procesos_cerrados = []

        # Recorre todos los procesos en ejecucion
        for proceso in psutil.process_iter(attrs=['pid', 'name']):
            try:
                nombre_proceso = proceso.info['name']
                # Si el nombre del proceso esta en la lista se cierra
                if nombre_proceso.lower() in [nombre.lower() for nombre in lista_procesos]:
                    pid = proceso.info['pid']
                    proceso_terminado = psutil.Process(pid)
                    try:
                        proceso_terminado.terminate()
                        try:
                            proceso_terminado.wait(timeout=5)
                            logger.info(f"Proceso cerrado (terminate): {nombre_proceso} (PID: {pid})")
                        except psutil.TimeoutExpired:
                            logger.warning(f"El proceso {nombre_proceso} (PID: {pid}) no respondió a terminate(). Se intentará kill().")
                            proceso_terminado.kill()
                            proceso_terminado.wait(timeout=5)
                            logger.info(f"Proceso cerrado forzosamente (kill): {nombre_proceso} (PID: {pid})")
                    except Exception as e:
                        logger.warning(f"No se pudo cerrar el proceso {nombre_proceso} (PID: {pid}): {e}")
                    procesos_cerrados.append(nombre_proceso)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.warning(f"No se pudo cerrar el proceso {nombre_proceso}: {e}")

        if not procesos_cerrados:
            logger.info("No se cerro ningun proceso.")
        else:
            logger.info(f"Procesos cerrados: {', '.join(procesos_cerrados)}")

    except Exception as e:
        logger.error(f"Error en cerrarProcesos: {e}")
    finally:
        logger.info("Fin del proceso ...")
        
        # Limpieza de archivos en una carpeta de manera recursiva
def limpiar_archivos_en_carpeta(ruta_carpeta, extensiones=None):
    """
    Elimina archivos en la carpeta especificada y en todas sus subcarpetas de manera recursiva.
    Si se especifica una lista de extensiones, solo elimina archivos con esas extensiones.
    :param ruta_carpeta: Ruta de la carpeta a limpiar.
    :param extensiones: Lista de extensiones a eliminar (ej. [".txt", ".csv"]). Si es None, elimina todos los archivos.
    """
    archivos_eliminados = []
    carpetas_vacias = []
    for root, dirs, files in os.walk(ruta_carpeta, topdown=False):
        for nombre_archivo in files:
            ruta_archivo = os.path.join(root, nombre_archivo)
            if extensiones:
                if any(nombre_archivo.lower().endswith(ext.lower()) for ext in extensiones):
                    try:
                        os.remove(ruta_archivo)
                        archivos_eliminados.append(ruta_archivo)
                        logger.info(f"Archivo eliminado: {ruta_archivo}")
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar el archivo {ruta_archivo}: {e}")
            else:
                try:
                    os.remove(ruta_archivo)
                    archivos_eliminados.append(ruta_archivo)
                    logger.info(f"Archivo eliminado: {ruta_archivo}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el archivo {ruta_archivo}: {e}")
        # Intentar eliminar carpetas vacías
        for nombre_carpeta in dirs:
            ruta_subcarpeta = os.path.join(root, nombre_carpeta)
            try:
                if not os.listdir(ruta_subcarpeta):
                    os.rmdir(ruta_subcarpeta)
                    carpetas_vacias.append(ruta_subcarpeta)
                    logger.info(f"Carpeta vacía eliminada: {ruta_subcarpeta}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar la carpeta {ruta_subcarpeta}: {e}")
    if not archivos_eliminados:
        logger.info("No se eliminaron archivos.")
    if carpetas_vacias:
        logger.info(f"Carpetas vacías eliminadas: {', '.join(carpetas_vacias)}")
    return archivos_eliminados
