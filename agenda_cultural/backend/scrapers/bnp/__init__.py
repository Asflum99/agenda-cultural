from .scraper import BnpScraper

get_bnp_movies = BnpScraper().get_movies


__all__ = ["get_bnp_movies"]
