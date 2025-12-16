"""
Servicio de ejecución concurrente de scrapers.

Este módulo se encarga de:
1. Orquestar la ejecución paralela de todos los scrapers definidos en el sistema.
2. Reportar el posible error que pueda mostrar uno o más scrapers, sin que este afecte a los demás.
3. Unificar los resultados en una única lista maestra de películas.
"""

import asyncio
from agenda_cultural.backend.scrapers import all_scrapers
from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.log_config import get_task_logger

logger = get_task_logger("scraper_service", "scraping.log")


async def fetch_all_movies() -> list[Movie]:
    """
    Ejecuta todos los scrapers disponibles en paralelo y unifica los resultados.

    Utiliza asyncio.gather para concurrencia. Si un scraper individual falla,
    se captura la excepción y se registran los errores sin detener el resto
    del proceso.

    Returns:
        list[Movie]: Lista combinada de todas las películas encontradas.
    """

    # Expresión generadora para recorrer la lista de funciones (all_scrapers).
    # La variable temporal 'scraper' toma cada función y al añadirle '()' la ejecutamos.
    # El asterisco '*' desempaqueta estas tareas iniciadas para que asyncio.gather las procese.
    # La variable 'results' almacena una lista de listas de películas por cada centro cultural. Por ejemplo:
    # results = [
    #   [Movie(1), Movie(2), Movie(3)],  # Éxito: Películas del primer centro cultural
    #   TimeoutError(...),               # Fallo: Excepción en el segundo centro cultural
    #   [Movie(1)]                       # Éxito: Películas del tercer centro cutlural
    # ]
    results: list[list[Movie] | BaseException] = await asyncio.gather(
        *(scraper() for scraper in all_scrapers),
        return_exceptions=True,
    )

    movies_scraped: list[Movie] = []

    # Procesamos la lista mixta de resultados (pueden ser listas o excepciones)
    for result in results:
        if isinstance(result, list):
            movies_scraped.extend(result)

        elif isinstance(result, Exception):
            logger.error(f"Falló uno de los scrapers: {result}")

    return movies_scraped
