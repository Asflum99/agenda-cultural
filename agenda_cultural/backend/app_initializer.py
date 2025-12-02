from .services import (
    has_upcoming_movies,
    cleanup_past_movies,
    save_movies_to_db,
    scrape_all_movies,
)


async def initialize_app():
    """Inicializa la aplicación: limpia BD o hace scraping según sea necesario"""
    if has_upcoming_movies():
        # Si hay películas futuras, solo limpia las pasadas
        cleanup_past_movies()
        print("BD actualizada - películas pasadas eliminadas")
    else:
        # Si no hay películas futuras, hace scraping completo
        print("BD vacía - iniciando scraping...")
        movies = await scrape_all_movies()
        save_movies_to_db(movies)
        print(f"Scraping completado - {len(movies)} películas guardadas")
