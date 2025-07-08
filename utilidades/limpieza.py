import psutil
import logging
import os
import platform
import subprocess

# Configuración del logger
logger = logging.getLogger("Utils - Limpieza Ambiente")

def cerrarProcesos(lista_procesos):
    """
    Cierra los procesos según los nombres proporcionados en la lista, forzando el cierre si es necesario.
    Utiliza comandos del sistema operativo para forzar el cierre.

    :param lista_procesos: Lista de nombres de procesos a cerrar (ej. ["chrome.exe", "excel.exe"]).
    """
   
    try:
        logger.info("Inicio del proceso ...")

        procesos_cerrados = []
        sistema_operativo = platform.system()

        # Recorre todos los procesos en ejecucion
        for proceso in psutil.process_iter(attrs=['pid', 'name']):
            try:
                nombre_proceso = proceso.info['name']
                # Si el nombre del proceso esta en la lista se cierra
                if nombre_proceso.lower() in [nombre.lower() for nombre in lista_procesos]:
                    pid = proceso.info['pid']
                    
                    # Intentar cerrar con psutil primero
                    proceso_terminado = psutil.Process(pid)
                    try:
                        proceso_terminado.terminate()
                        try:
                            proceso_terminado.wait(timeout=3)
                            logger.info(f"Proceso cerrado (terminate): {nombre_proceso} (PID: {pid})")
                            procesos_cerrados.append(nombre_proceso)
                            continue
                        except psutil.TimeoutExpired:
                            logger.warning(f"El proceso {nombre_proceso} (PID: {pid}) no respondió a terminate(). Se intentará con comando del SO.")
                    except Exception as e:
                        logger.warning(f"No se pudo cerrar el proceso {nombre_proceso} (PID: {pid}) con psutil: {e}")

                    # Forzar cierre con comandos del sistema operativo
                    try:
                        if sistema_operativo == "Windows":
                            # Comando para Windows
                            comando = f'taskkill /F /PID {pid}'
                            resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=10)
                            if resultado.returncode == 0:
                                logger.info(f"Proceso cerrado forzosamente (taskkill): {nombre_proceso} (PID: {pid})")
                                procesos_cerrados.append(nombre_proceso)
                            else:
                                logger.warning(f"No se pudo cerrar {nombre_proceso} (PID: {pid}) con taskkill: {resultado.stderr}")
                        
                        elif sistema_operativo == "Darwin":  # macOS
                            # Comando para macOS
                            comando = f'kill -9 {pid}'
                            resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=10)
                            if resultado.returncode == 0:
                                logger.info(f"Proceso cerrado forzosamente (kill -9): {nombre_proceso} (PID: {pid})")
                                procesos_cerrados.append(nombre_proceso)
                            else:
                                logger.warning(f"No se pudo cerrar {nombre_proceso} (PID: {pid}) con kill -9: {resultado.stderr}")
                        
                        elif sistema_operativo == "Linux":
                            # Comando para Linux
                            comando = f'kill -9 {pid}'
                            resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=10)
                            if resultado.returncode == 0:
                                logger.info(f"Proceso cerrado forzosamente (kill -9): {nombre_proceso} (PID: {pid})")
                                procesos_cerrados.append(nombre_proceso)
                            else:
                                logger.warning(f"No se pudo cerrar {nombre_proceso} (PID: {pid}) con kill -9: {resultado.stderr}")
                        
                        else:
                            logger.warning(f"Sistema operativo no reconocido: {sistema_operativo}")
                            
                    except subprocess.TimeoutExpired:
                        logger.error(f"Timeout al intentar cerrar {nombre_proceso} (PID: {pid}) con comando del SO")
                    except Exception as e:
                        logger.error(f"Error al ejecutar comando del SO para {nombre_proceso} (PID: {pid}): {e}")

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.warning(f"No se pudo acceder al proceso: {e}")

        if not procesos_cerrados:
            logger.info("No se cerró ningún proceso.")
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
