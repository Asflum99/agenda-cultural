import reflex as rx
import re
from agenda_cultural.states.alianza_francesa.scraper import get_movies


class AlianzaFrancesaState(rx.State):
    alianza_movies: list[dict] = []
    alianza_movies_loaded: bool = False

    def _extract_day(self, date_str: str) -> int:
        """Helper para extraer el día de una fecha"""
        match = re.search(r"(\d+)\s+de", date_str)
        return int(match.group(1)) if match else 999

    def _order_movies(self, movies: list[dict]) -> list[dict]:
        """Ordena las películas por fecha de proyección"""
        return sorted(movies, key=lambda movie: self._extract_day(movie["date"]))

    @rx.event(background=True)
    async def load_movies(self):
        if self.alianza_movies_loaded:
            return
        if movies := await get_movies():
            async with self:
                self.alianza_movies.extend(movies)
                self.alianza_movies = self._order_movies(self.alianza_movies)
                self.alianza_movies_loaded = True
