import reflex as rx
from datetime import date
from sqlalchemy import select, delete
import asyncio

from agenda_cultural.models import Movie
from agenda_cultural.states.alianza_francesa.state import load_movies as load_af_movies
from agenda_cultural.states.bnp.state import load_movies as load_bnp_movies
from agenda_cultural.states.ccpucp.state import load_movies as load_ccpucp_movies


async def scrape_and_update_db():
    try:
        movies = await scrape_movies()

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
        print(e)


async def initialize_app():
    with rx.session() as session:

        today = date.today()
        future_movies_query = select(Movie).where(
            Movie.date >= today.strftime("%Y-%m-%d")
        )
        future_movies = len(session.exec(future_movies_query).all())

        if future_movies > 0:
            past_movies_query = delete(Movie).where(
                Movie.date < today.strftime("%Y-%m-%d")
            )
            session.exec(past_movies_query)
            session.commit()
        else:
            await scrape_and_update_db()


async def scrape_movies():
    movies = []

    results = await asyncio.gather(
        load_af_movies(movies),
        load_bnp_movies(movies),
        load_ccpucp_movies(movies),
        return_exceptions=True,
    )

    for result in results:
        if isinstance(result, list):
            movies.extend(result)
        elif isinstance(result, Exception):
            print(f"Error en scraper: {result}")

    return movies
