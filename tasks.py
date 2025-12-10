import asyncio
from agenda_cultural.backend import initialize_app
from agenda_cultural.backend import get_task_logger

logger = get_task_logger("maintenance_orchestrator", "scraping.log")


async def run_nightly_maintenance():
    logger.info("--- Iniciando mantenimiento nocturno ---")
    try:
        await initialize_app()
        logger.info("--- Mantenimiento finalizado con ÉXITO ---")
    except Exception as e:
        logger.error(f"--- ERROR CRÍTICO en mantenimiento: {e} ---")


if __name__ == "__main__":
    asyncio.run(run_nightly_maintenance())
