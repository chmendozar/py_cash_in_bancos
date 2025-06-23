import logging
from pathlib import Path

def init_logger(ruta_log: str, nivel: int = logging.INFO) -> None:
    """
    Inicializa el logger con la configuración básica
    
    Args:
        ruta_log (str): Ruta del archivo de log
        nivel (int): Nivel de logging (default: logging.INFO)
    """
    logging.basicConfig(
        level=nivel,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Path(ruta_log)),
            logging.StreamHandler()
        ]
    ) 