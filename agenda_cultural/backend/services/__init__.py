"""
Fachada de servicios del backend.

Expone las funciones principales de la lógica de negocio (Scraping y Base de Datos)
para que sean consumidas fácilmente por el orquestador u otros módulos,
ocultando la complejidad de la estructura interna de archivos.
"""

from .scraper_service import fetch_all_movies
from .database_service import (
    sync_movies_to_db,
    cleanup_past_movies,
)


__all__ = [
    "fetch_all_movies",
    "sync_movies_to_db",
    "cleanup_past_movies",
]
