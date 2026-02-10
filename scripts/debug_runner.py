#!/usr/bin/env python3
"""
Script de debugging dinámico.
Carga automáticamente las clases de scrapers basándose en cultural_centers.py
y la estructura de carpetas estándar.
"""

import asyncio
import importlib
import os
import sys
from pathlib import Path

# Añadir el raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# --- IMPORTACIÓN DE CONSTANTE ---
try:
    from agenda_cultural.shared import CULTURAL_CENTERS
except ImportError as e:
    print("\n" + "!" * 60)
    print("🔥 ERROR CRÍTICO DE IMPORTACIÓN")
    print("!" * 60)
    print("\n❌ No se pudo importar 'CULTURAL_CENTERS'.")
    print("   El script de debugging no puede continuar sin esta configuración.")

    print(f"\n🔍 Detalle del error: {e}")

    print("\n💡 Posibles causas:")
    print("   1. La ruta 'agenda_cultural.shared.cultural_centers' es incorrecta.")
    print("   2. Te falta un archivo '__init__.py' en alguna carpeta intermedia.")
    print("   3. El 'sys.path' no está apuntando a la raíz del proyecto.")

    print("!" * 60 + "\n")
    sys.exit(1)


def get_scraper_class(key: str):
    """
    Importa dinámicamente la clase del scraper.
    """
    folder_name = key

    # 1. Construir nombre de clase (alianza_francesa -> AlianzaFrancesaScraper)
    class_name = (
        "".join(word.capitalize() for word in folder_name.split("_")) + "Scraper"
    )

    # 2. Importación dinámica
    module_path = f"agenda_cultural.backend.scrapers.{folder_name}.scraper"

    try:
        # Esto equivale a: from agenda_cultural... import module
        module = importlib.import_module(module_path)
        # Esto obtiene la clase del módulo
        scraper_class = getattr(module, class_name)
        return scraper_class
    except (ImportError, AttributeError) as e:
        print(f"⚠️  No se pudo cargar el scraper para '{key}': {e}")
        return None


def detect_scraper() -> str | None:
    """Detecta el scraper basado en el archivo abierto en Neovim."""
    current_file = os.getenv("NVIM_CURRENT_FILE", "")
    if not current_file:
        return None

    path_str = str(Path(current_file).absolute())

    # Iteramos sobre las llaves de tu config centralizada
    for key in CULTURAL_CENTERS:
        folder_name = key
        # Chequeamos si el nombre de la carpeta está en la ruta del archivo
        if f"scrapers/{folder_name}" in path_str:
            return key
    return None


def show_menu(current_detected: str | None) -> str:
    """Menú dinámico basado en CULTURAL_CENTERS."""
    print("\n" + "🎯" * 25)
    print("  DEBUGGER DE SCRAPERS".center(50))
    print("🎯" * 25 + "\n")

    # Ordenamos las opciones para que siempre salgan igual
    options = sorted(list(CULTURAL_CENTERS.keys()))

    for i, key in enumerate(options, 1):
        name = CULTURAL_CENTERS[key]["name"]
        marker = " ← (Detectado)" if key == current_detected else ""
        print(f"  [{i}] {name}{marker}")

    print("\n  [q] Salir\n")

    while True:
        choice = input("  Selecciona un scraper: ").strip().lower()
        if choice == "q":
            sys.exit(0)
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print("  ❌ Opción inválida.")


async def run_debug(scraper_key: str):
    """Instancia y ejecuta el scraper dinámicamente."""
    os.environ["SCRAPER_HEADLESS"] = (
        "false"  # Fuerza a que el navegador sea visible durante debugging
    )
    info = CULTURAL_CENTERS[scraper_key]
    print(f"\n🚀 Iniciando Debugger: {info['name']}")
    print("=" * 50 + "\n")

    # Obtenemos la clase al vuelo
    ScraperClass = get_scraper_class(scraper_key)

    if not ScraperClass:
        print(f"❌ Error crítico: No se encontró la clase para {scraper_key}")
        return

    # Instanciamos y ejecutamos
    try:
        scraper = ScraperClass()
        movies = await scraper.get_movies()

        print("\n" + "=" * 50)
        print(f"✅ Finalizado: {len(movies)} películas encontradas")
        print("=" * 50 + "\n")

        # Mostrar todas las películas con formato ordenado
        if movies:
            for i, movie in enumerate(movies, 1):
                print(f"🎬 Película {i}")
                print(f"   Título: {movie.title}")
                print(f"   Ubicación: {movie.location}")
                print(f"   Fecha: {movie.date}")
                print(f"   Centro: {movie.center}")
                print(f"   Póster: {movie.poster_url or 'N/A'}")
                print(f"   URL: {movie.source_url or 'N/A'}")
                print("   " + "─" * 40)
                print()
        else:
            print("   ⚠️  No se encontraron películas.")

        print("=" * 50 + "\n")

    except Exception as e:
        print(f"🔥 Error ejecutando el scraper: {e}")
        # Re-lanzamos para que el debugger de Neovim lo capture si está activo
        raise e


async def main():
    scraper_to_run = detect_scraper()

    if not scraper_to_run:
        scraper_to_run = show_menu(None)
    else:
        # Validamos visualmente
        name = CULTURAL_CENTERS[scraper_to_run]["name"]
        print(f"✨ Auto-detección: {name}")

    await run_debug(scraper_to_run)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Abortado.")
        sys.exit(0)
