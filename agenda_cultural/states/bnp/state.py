import reflex as rx

from agenda_cultural.states.bnp.scraper import get_movies


async def load_movies(movies: list[dict]):
    if movies_scrapped := await get_movies():
        movies.extend(movies_scrapped)
