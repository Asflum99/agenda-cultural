"""
Servicios de manipulación de datos (Base de Datos).

Este módulo gestiona las operaciones CRUD (Create, Read, Update, Delete)
relacionadas con las películas. Sus responsabilidades son:
1. Limpieza: Borrar funciones pasadas para no llenar la DB de basura.
2. Actualización: Guardar nuevas películas aplicando lógica de desduplicación.
"""

import reflex as rx
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import delete, select, Session
from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.log_config import get_task_logger

# Usamos el logger 'database_service' pero guardamos en el mismo archivo 'scraping.log'
# para tener la historia completa en un solo lugar.
# Por ejemplo, la ejecución de un scraper se guarda en 'scraping.log'. Luego se ejecuta la
# interacción con la BD. Lo mejor es ver en un mismo archivo log si esos 2 pasos fueron éxitosos.
logger = get_task_logger("database_service", "scraping.log")


def cleanup_past_movies():
    """
    Elimina películas ya proyectadas de la base de datos.

    Compara la fecha de la función con la hora actual de Lima.
    Si la función ya ocurrió, se borra para mantener la base de datos ligera.
    """

    logger.info("Iniciando limpieza de funciones pasadas en DB...")
    with rx.session() as session:
        # Obtenemos hora actual en Lima y quitamos info de zona horaria (naive)
        # para que coincida con el formato de la base de datos SQL.
        now_clean = datetime.now(ZoneInfo("America/Lima")).replace(tzinfo=None)

        statement = delete(Movie).where(Movie.date < now_clean)  # pyright: ignore
        session.exec(statement)
        session.commit()


def _get_existing_signatures(session: Session) -> set[tuple]:
    """Obtiene firmas (Cine, Título, Fecha) para comparación rápida."""
    statement = select(Movie.center, Movie.title, Movie.date)
    results = session.exec(statement).all()
    return {(center, title, date) for center, title, date in results}


def _filter_new_movies(scraped_movies: list[Movie], session: Session) -> list[Movie]:
    """Filtra las películas scrapeadas para quedarse solo con las nuevas que no están
    en la base de datos.

    Returns:
        list: Lista con las películas nuevas que se encontraron.
    """
    existing_signatures = _get_existing_signatures(session)
    new_movies = []

    for movie in scraped_movies:
        signature = (movie.center, movie.title, movie.date)
        if signature not in existing_signatures:
            new_movies.append(movie)

    return new_movies


def _save_new_movies_to_db(new_movies: list[Movie], session: Session) -> int:
    """Guarda las nuevas películas en la base de datos, si es que las hubiese.

    Returns:
        int: Número de películas nuevas guardadas en la base de datos.
    """
    if not new_movies:
        return 0

    session.add_all(new_movies)
    session.commit()
    return len(new_movies)


def sync_movies_to_db(scraped_movies: list[Movie]) -> int:
    """
    Sincroniza la lista de películas obtenidas con la base de datos.
    Garantiza que no se inserten duplicados.

    Returns:
        int: Número de películas nuevas guardadas en la base de datos.
    """
    with rx.session() as session:
        # 1. Identificar lo nuevo
        new_movies_to_save = _filter_new_movies(scraped_movies, session)

        # 2. Guardar
        count = _save_new_movies_to_db(new_movies_to_save, session)

        return count
