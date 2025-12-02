from .alianza_francesa import get_af_movies
from .bnp import get_bnp_movies
from .ccpucp import get_ccpucp_movies

all_scrapers = [get_af_movies, get_bnp_movies, get_ccpucp_movies]
