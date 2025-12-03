import asyncio
from agenda_cultural.backend.app_initializer import initialize_app
from agenda_cultural.backend.logger import configure_scraping_logger

logger = configure_scraping_logger()

async def run_nightly_maintenance():
    logger.info("--- Iniciando mantenimiento nocturno ---")
    try:
        await initialize_app()
        logger.info("--- Mantenimiento finalizado con ÉXITO ---")
    except Exception as e:
        logger.error(f"--- ERROR CRÍTICO en mantenimiento: {e} ---")


if __name__ == "__main__":
    asyncio.run(run_nightly_maintenance())
