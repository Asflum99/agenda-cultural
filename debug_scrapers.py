import asyncio
import logging
import sys
import argparse

# --- IMPORTS DE TUS SCRAPERS ---
# Asegúrate de importar aquí todos los scrapers que vayas creando
from agenda_cultural.backend.scrapers.lum import LumScraper
from agenda_cultural.backend.scrapers.alianza_francesa import AlianzaFrancesaScraper
from agenda_cultural.backend.scrapers.bnp import BnpScraper
from agenda_cultural.backend.scrapers.ccpucp import CcpucpScraper
# from agenda_cultural.scrapers.ccpucp_scraper import CcpucpScraper (cuando lo tengas)

# --- MAPA DE SCRAPERS ---
# Aquí registras el nombre clave que usarás en la terminal y la Clase correspondiente
SCRAPERS = {
    "lum": LumScraper,
    "af": AlianzaFrancesaScraper,
    "bnp": BnpScraper,
    "ccpucp": CcpucpScraper,
}

# Configuración de Logging para ver todo en la consola
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def test_single_scraper(scraper_name: str):
    """Función genérica para probar cualquier scraper."""

    scraper_class = SCRAPERS.get(scraper_name)

    if not scraper_class:
        logger.error(f"❌ No existe el scraper '{scraper_name}'.")
        logger.info(f"Opciones disponibles: {list(SCRAPERS.keys())}")
        return

    print(f"\n🚀 INICIANDO TEST: {scraper_name.upper()}...")

    try:
        # Instanciamos la clase dinámicamente
        scraper = scraper_class()

        # Ejecutamos
        movies = await scraper.get_movies()

        print("\n🎬 RESULTADOS FINALIZADOS")
        print(f"Total encontrado: {len(movies)} películas.")
        print("=" * 60)

        for i, movie in enumerate(movies, 1):
            print(f"\n🎥 PELÍCULA #{i}")
            print(f"   Title    : {movie.title}")
            print(f"   Date     : {movie.date}")
            print(f"   Location : {movie.location or 'N/A'}")
            print(f"   Center   : {movie.center}")
            print(f"   Link     : {movie.source_url}")
            print("-" * 30)

    except Exception as e:
        logger.critical(f"💥 El scraper falló con error: {e}", exc_info=True)


if __name__ == "__main__":
    # Configuración de argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description="Herramienta de depuración de scrapers."
    )
    parser.add_argument(
        "scraper", type=str, help="Nombre clave del scraper a probar (ej: lum, af)"
    )

    args = parser.parse_args()

    # Ejecutar
    asyncio.run(test_single_scraper(args.scraper))
