import logging
from logging.handlers import RotatingFileHandler
import sys
import os

if not os.path.exists("logs"):
    os.makedirs("logs")


def get_task_logger(logger_name: str, log_filename: str = "app.log"):
    """
    Crea un logger configurado que guarda en logs/log_filename
    """
    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"
    )

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        return logger

    file_path = os.path.join("logs", log_filename)

    file_handler = RotatingFileHandler(
        file_path,
        mode="a",
        maxBytes=5 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",
        delay=False,
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)  # En archivo solo INFO o superior

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)  # En consola todo

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
