import os
import datetime
from configobj import ConfigObj

def cargar_configuracion():
    try:
        config = ConfigObj("config/config.ini")  # Use forward slashes for path

        # Check if required sections and keys exist
        if "rutas" not in config:
            raise KeyError("Section 'rutas' not found in config file")
        if "ruta_log" not in config["rutas"]:
            raise KeyError("Key 'ruta_log' not found in 'rutas' section")
        if "archivos" not in config:
            raise KeyError("Section 'archivos' not found in config file") 
        if "archivos_log" not in config["archivos"]:
            raise KeyError("Key 'archivos_log' not found in 'archivos' section")

        carpeta_log = os.path.normpath(config["rutas"]["ruta_log"])
        archivo_log = config["archivos"]["archivos_log"]

        fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_log = archivo_log.replace("ddmmyy_hhmmss", fecha)

        config["archivos"]["archivos_log"] = os.path.join(carpeta_log, archivo_log)

        return config
    except Exception as e:
        raise e