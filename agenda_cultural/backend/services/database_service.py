import reflex as rx
from datetime import date, datetime
from sqlalchemy import select, delete
from zoneinfo import ZoneInfo
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
        now = datetime.now(ZoneInfo("America/Lima"))
        query = select(Movie).filter(Movie.date > now).limit(1)
        future_movie = session.exec(query).first()  # type: ignore[call-overload]
        return future_movie is not None


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
