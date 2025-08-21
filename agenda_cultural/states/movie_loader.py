import reflex as rx
import asyncio
from agenda_cultural.states.alianza_francesa.state import load_movies as load_af_movies
from agenda_cultural.states.bnp.state import load_movies as load_bnp_movies
from agenda_cultural.states.ccpucp.state import load_movies as load_ccpucp_movies


class MovieState(rx.State):
    movies: list[dict] = []

    async def load_all_movies(self):
        """Disparar scrapers en paralelo"""
        results = await asyncio.gather(
            load_af_movies(self.movies),
            load_bnp_movies(self.movies),
            load_ccpucp_movies(self.movies),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, list):
                self.movies.extend(result)
            elif isinstance(result, Exception):
                print(f"Error en scraper: {result}")

        return self.movies
