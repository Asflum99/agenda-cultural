import asyncio
from agenda_cultural.backend.scrapers.alianza_francesa import get_af_movies
from agenda_cultural.backend.scrapers.bnp import get_bnp_movies
from agenda_cultural.backend.scrapers.ccpucp import get_ccpucp_movies


async def scrape_all_movies() -> list[dict]:
    """Ejecuta todos los scrapers en paralelo"""
    results = await asyncio.gather(
        get_af_movies(),
        get_bnp_movies(),
        get_ccpucp_movies(),
        return_exceptions=True,
    )

    movies = []
    for result in results:
        if isinstance(result, list) and result:
            movies.extend(result)
        elif isinstance(result, Exception):
            print(f"Error en scraper: {result}")

    return movies
