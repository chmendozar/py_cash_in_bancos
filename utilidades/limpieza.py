import psutil
import logging

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