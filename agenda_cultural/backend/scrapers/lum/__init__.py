from .scraper import LumScraper

get_lum_movies = LumScraper().get_movies

__all__ = ["get_lum_movies"]
