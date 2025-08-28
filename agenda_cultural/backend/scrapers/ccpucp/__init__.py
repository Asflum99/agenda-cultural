from .scraper import CcpucpScraper

get_ccpucp_movies = CcpucpScraper().get_movies

__all__ = ["get_ccpucp_movies"]
