import reflex as rx
from datetime import datetime
from zoneinfo import ZoneInfo
from agenda_cultural.backend.models import Movies


def cleanup_past_movies():
    """Elimina películas ya proyectadas de la base de datos"""
    with rx.session() as session:
        today_aware = datetime.now(ZoneInfo("America/Lima"))
        today_naive = today_aware.replace(tzinfo=None)
        movies = session.exec(Movies.select().where(Movies.date < today_naive)).all() # pyright: ignore
        for movie in movies:
            session.delete(movie)
        session.commit()


def has_upcoming_movies() -> bool:
    """Verifica si hay películas por proyectarse en la BD"""
    with rx.session() as session:
        now_aware = datetime.now(ZoneInfo("America/Lima"))
        now_naive = now_aware.replace(tzinfo=None)
        query = (
            Movies.select()
            .where(Movies.date is not None, Movies.date > now_naive) # pyright: ignore
            .limit(1)
        )
        future_movie = session.exec(query).first()
        return future_movie is not None


def save_movies_to_db(movies: list[Movies]):
    """Guarda lista de películas en la BD"""
    try:
        with rx.session() as session:
            db_movies = [
                Movies(
                    title=movie.title,
                    location=movie.location,
                    date=movie.date,
                    center=movie.center,
                )
                for movie in movies
            ]
            session.add_all(db_movies)
            session.commit()
    except Exception as e:
        print(f"Error guardando en BD: {e}")
