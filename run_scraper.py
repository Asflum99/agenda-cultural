"""
Script de ejecución para el proceso de scraping.

Este archivo es invocado automáticamente por el servicio del sistema (Systemd)
cada medianoche. Su única responsabilidad es iniciar el orquestador y reportar
el estado de salida al sistema operativo.
"""

import asyncio
import sys
from agenda_cultural.backend import run_scraping_pipeline
from agenda_cultural.backend import get_task_logger

# Usamos 'scheduler' como nombre para diferenciar que esto lo lanzó el sistema
logger = get_task_logger("scheduler", "scraping.log")


async def main():
    """
    Función principal que envuelve el pipeline en un manejo de errores de alto nivel.
    """
    logger.info("Iniciando ejecución programada del Scraper")

    try:
        await run_scraping_pipeline()
        logger.info("Ejecución programada finalizada con ÉXITO")

    except Exception as e:
        logger.critical(f"ERROR CRÍTICO DEL SISTEMA: {e}", exc_info=True)
        sys.exit(
            1
        )  # Salimos con error para que Systemd marque el servicio como 'Failed'


if __name__ == "__main__":
    asyncio.run(main())
