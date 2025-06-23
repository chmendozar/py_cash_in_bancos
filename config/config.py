import os
import datetime
from configobj import ConfigObj

def cargar_configuracion():
    try:
        config = ConfigObj("config\config.ini")

        carpeta_log = os.path.normpath(config["rutas"]["ruta_log"])
        archivo_log = config["archivos"]["archivos_log"]

        fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_log = archivo_log.replace("ddmmyy_hhmmss",fecha)

        config["archivos"]["archivos_log"] = os.path.join(carpeta_log, archivo_log)

        return config
    except Exception as e:
        raise e