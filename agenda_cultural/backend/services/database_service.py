import reflex as rx
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import delete, select
from agenda_cultural.backend.models import Movies


def cleanup_past_movies():
    """Elimina películas ya proyectadas de la base de datos"""
    with rx.session() as session:
        now_clean = datetime.now(ZoneInfo("America/Lima")).replace(tzinfo=None)

        statement = delete(Movies).where(Movies.date < now_clean)  # pyright: ignore
        session.exec(statement)
        session.commit()


def save_movies_to_db(movies: list[Movies]):
    """Guarda lista de películas en la BD"""
    with rx.session() as session:
        new_count = 0

        for movie in movies:
            existing_movie = session.exec(
                select(Movies).where(
                    Movies.center == movie.center,
                    Movies.title == movie.title,
                    Movies.date == movie.date,
                )
            ).first()

            if existing_movie is None:
                session.add(movie)
                new_count += 1

        session.commit()
