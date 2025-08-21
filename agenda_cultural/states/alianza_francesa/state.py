import reflex as rx
import re
from agenda_cultural.states.alianza_francesa.scraper import get_movies


def _extract_day(date_str: str) -> int:
    """Helper para extraer el día de una fecha"""
    match = re.search(r"(\d+)\s+de", date_str)
    return int(match.group(1)) if match else 999


def _order_movies(movies: list[dict]) -> list[dict]:
    """Ordena las películas por fecha de proyección"""
    return sorted(movies, key=lambda movie: _extract_day(movie["date"]))


async def load_movies(movies: list[dict]):
    if movies_scrapped := await get_movies():
        movies_scrapped = _order_movies(movies_scrapped)
        movies.extend(movies_scrapped)
