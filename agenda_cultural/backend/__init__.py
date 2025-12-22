"""
Interfaz pública del paquete Backend.

Centraliza los componentes accesibles desde otras capas de la aplicación (Frontend),
como los modelos de datos y el orquestador de scraping.
"""

from .log_config import get_task_logger
from .models import Movie
from .scraping_orchestrator import run_scraping_pipeline

# Define explícitamente qué se exporta cuando alguien hace:
# "from agenda_cultural.backend import *"
__all__ = ["Movie", "get_task_logger", "run_scraping_pipeline"]
