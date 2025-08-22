from .scraper_service import scrape_all_movies
from .database_service import (
    has_upcoming_movies,
    save_movies_to_db,
    cleanup_past_movies,
)
