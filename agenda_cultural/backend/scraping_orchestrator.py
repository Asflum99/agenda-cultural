"""
Orquestador del flujo de trabajo de actualización de datos (Scraping Pipeline).

Este módulo coordina la secuencia de ejecución para mantener la base de datos al día:
1. Depuración de funciones que ya se proyectaron.
2. Extracción de nueva información (Scraping).
3. Guardar las nuevas funciones en la base de datos, si es que llega a encontrar alguna.
"""

from .services import (
    cleanup_past_movies,
    sync_movies_to_db,
    fetch_all_movies,
)
from .log_config import get_task_logger

logger = get_task_logger("scraper_orchestrator", "scraping.log")


async def run_scraping_pipeline():
    """
    Ejecuta el ciclo completo de actualización de la base de datos.

    Maneja el flujo de limpieza, scraping y guardado. Si ocurre un error
    crítico en cualquiera de las etapas, lo registra y detiene el flujo
    para evitar corrupción de datos.
    """
    try:
        cleanup_past_movies()

        movies_scraped = await fetch_all_movies()

        new_movies_count = sync_movies_to_db(movies_scraped)

        if new_movies_count > 0:
            logger.info(
                f"Se añadieron {new_movies_count} películas (de {len(movies_scraped)} encontradas)."
            )
        else:
            logger.info(
                f"De las {len(movies_scraped)} películas encontradas, todas ya están en la BD. No se agregaron nuevas películas."
            )

    except Exception as e:
        logger.critical(
            f"Error crítico en el orquestador de scraping: {e}", exc_info=True
        )
