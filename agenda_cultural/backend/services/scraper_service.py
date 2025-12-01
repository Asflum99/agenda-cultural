import asyncio
from agenda_cultural.backend.scrapers import all_scrapers
from agenda_cultural.backend.models import Movies


async def scrape_all_movies() -> list[Movies]:
    """Ejecuta todos los scrapers en paralelo"""
    results = await asyncio.gather(
        *(scraper() for scraper in all_scrapers),
        return_exceptions=True,
    )

    movies: list[Movies] = []
    for result in results:
        if isinstance(result, list) and result:
            movies.extend(result)
        elif isinstance(result, Exception):
            print(f"Error en scraper: {result}")

    return movies
