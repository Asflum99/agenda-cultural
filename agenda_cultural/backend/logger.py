import logging
from logging.handlers import RotatingFileHandler
import sys

def configure_scraping_logger():
    """
    Configura y devuelve un logger con rotación de archivos.
    """
    # 1. Definir el nombre del archivo y formato
    log_filename = 'scraping.log'
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')

    # 2. Obtener el logger raíz o uno específico
    logger = logging.getLogger("agenda_cultural_scraper")
    logger.setLevel(logging.DEBUG)

    # Evitar duplicar handlers si la función se llama varias veces
    if logger.hasHandlers():
        return logger

    # 3. Handler de Archivo (Con Rotación) - Guarda el historial
    file_handler = RotatingFileHandler(
        log_filename,
        mode='a',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=2,         # Guarda log, log.1, log.2
        encoding='utf-8',
        delay=False
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    # 4. Handler de Consola (Stream) - Para ver los logs en la terminal/AWS CloudWatch
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)

    # 5. Agregar ambos al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
