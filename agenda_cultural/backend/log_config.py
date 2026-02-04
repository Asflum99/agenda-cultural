"""
Módulo de configuración centralizada de Logging.

Provee una fábrica de loggers que estandariza:
1. El formato de salida (Timestamp - Nivel - Origen - Mensaje).
2. La rotación de archivos (para evitar llenar el disco).
3. La salida dual: Archivo (INFO) y Consola (DEBUG).
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import boto3
import watchtower

REGION = os.getenv("AWS_REGION", "us-east-1")


def get_task_logger(logger_name: str, log_filename: str) -> logging.Logger:
    """
    Configura y devuelve una instancia de Logger con handlers rotativos y de consola.
    Los logs se guardarán en la carpeta 'logs/' en la raíz del proyecto.

    Args:
        logger_name (str): Identificador del logger.
        log_filename (str): Nombre del archivo en la carpeta 'logs/'.

    Returns:
        logging.Logger: El objeto logger configurado y listo para usar.
    """
    # Asegurar la extensión ".log" en el archivo
    if not log_filename.strip().lower().endswith(".log"):
        log_filename = f"{log_filename}.log"

    # 1. Validación: Evitar duplicidad de handlers
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # 2. Configuración de Rutas con Pathlib (Robusto y Absoluto)
    # Navegamos desde: backend/log_config.py -> backend -> agenda_cultural -> RAÍZ
    base_dir = Path(__file__).resolve().parent.parent.parent
    logs_dir = base_dir / "logs"

    # Crea la carpeta si no existe (incluyendo padres si fuera necesario)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # 3. Formato estandarizado
    log_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 4. Handler de Archivo (Rotativo)
    file_path = logs_dir / log_filename

    file_handler = RotatingFileHandler(
        file_path,
        mode="a",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=2,
        encoding="utf-8",
        delay=False,
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    # 5. Handler de Consola (Stream)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)

    # 6. Asignación final
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    enable_cloudwatch = os.getenv("ENABLE_CLOUDWATCH_LOGS", "false").lower() == "true"
    if enable_cloudwatch:
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group_name="agenda-cultural-scrapers",
            log_stream_name=logger_name,
            boto3_client=boto3.client("logs", region_name=REGION),
        )
        cloudwatch_handler.setFormatter(log_formatter)
        cloudwatch_handler.setLevel(logging.INFO)
        logger.addHandler(cloudwatch_handler)

    return logger
