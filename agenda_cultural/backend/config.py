"""
Configuración del entorno y variables de conexión a servicios externos.

Carga las variables de entorno desde el archivo .env y define las URLs base
para la API de The Movie Database (TMDB).
"""

import os

from dotenv import load_dotenv

from agenda_cultural.backend.log_config import get_task_logger

logger = get_task_logger("config_loader", "system.log")

# Cargamos las variables de entorno cuando se importa este archivo
load_dotenv()

# Configuración TMDB
TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w342"

# Evaluamos si hay token
_token = os.getenv("TMDB_TOKEN")

if not _token:
    # Si no hay token, lanzamos un warning para corregirlo.
    # Esto implica que no se descargarán los pósters de las películas
    logger.warning("TMDB_TOKEN no configurado. La aplicación funcionará sin pósters.")
    _token = ""

TMDB_TOKEN: str = _token
