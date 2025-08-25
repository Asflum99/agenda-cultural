import reflex as rx
from datetime import datetime
from zoneinfo import ZoneInfo
from agenda_cultural.backend.models import Movie


def cleanup_past_movies():
    """Elimina películas ya proyectadas de la base de datos"""
    with rx.session() as session:
        today = datetime.now(ZoneInfo("America/Lima"))
        movies = session.exec(Movie.select().where(Movie.date < today)).all()
        for movie in movies:
            session.delete(movie)
        session.commit()


def has_upcoming_movies() -> bool:
    """Verifica si hay películas por proyectarse en la BD"""
    with rx.session() as session:
        now = datetime.now(ZoneInfo("America/Lima"))
        query = Movie.select().where(Movie.date > now).limit(1)
        future_movie = session.exec(query).first()
        return future_movie is not None


def save_movies_to_db(movies: list[Movie]):
    """Guarda lista de películas en la BD"""
    try:
        with rx.session() as session:
            db_movies = [
                Movie(
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
