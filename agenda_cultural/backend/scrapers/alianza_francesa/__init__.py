from .scraper import AlianzaFrancesaScraper

get_af_movies = AlianzaFrancesaScraper().get_movies

__all__ = ["get_af_movies"]
