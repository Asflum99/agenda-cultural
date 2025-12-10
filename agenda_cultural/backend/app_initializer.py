from .services import (
    cleanup_past_movies,
    save_movies_to_db,
    scrape_all_movies,
)
from .log_config import get_task_logger

logger = get_task_logger("scraper_worker", "scraping.log")


async def initialize_app():
    logger.info("--- 1. Iniciando limpieza de base de datos ---")
    cleanup_past_movies()

    logger.info("--- 2. Iniciando scrapping de carteleras ---")
    fresh_movies = await scrape_all_movies()

    logger.info(f"--- 3. Guardando datos (Encontrados: {len(fresh_movies)})")
    save_movies_to_db(fresh_movies)
