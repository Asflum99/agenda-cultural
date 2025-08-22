import reflex as rx
from datetime import date
from sqlalchemy import select, delete
from agenda_cultural.backend.models import Movie


def cleanup_past_movies():
    """Elimina películas ya proyectadas de la base de datos"""
    with rx.session() as session:
        today = date.today()
        past_movies_query = delete(Movie).where(Movie.date < today.strftime("%Y-%m-%d"))
        session.exec(past_movies_query)
        session.commit()


def has_upcoming_movies() -> bool:
    """Verifica si hay películas por proyectarse en la BD"""
    with rx.session() as session:
        today = date.today()
        future_movies_query = select(Movie).where(
            Movie.date >= today.strftime("%Y-%m-%d")
        )
        future_movies = len(session.exec(future_movies_query).all())
        return future_movies > 0


def save_movies_to_db(movies: list[dict]):
    """Guarda lista de películas en la BD"""
    try:
        with rx.session() as session:
            for movie in movies:
                db_movie = Movie(
                    title=movie["title"],
                    location=movie["location"],
                    date=movie["date"],
                    center=movie["center"],
                )
                session.add(db_movie)
            session.commit()
    except Exception as e:
        print(f"Error guardando en BD: {e}")
