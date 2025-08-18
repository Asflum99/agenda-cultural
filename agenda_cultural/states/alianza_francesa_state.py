import reflex as rx
from agenda_cultural.states.scrapers.alianza_francesa import get_movies


class AlianzaFrancesaState(rx.State):
    alianza_movies = []
    alianza_movies_loaded = False

    async def load_movies(self):
        if self.alianza_movies_loaded:
            return
        if movies := await get_movies():
            for movie in movies:
                self.alianza_movies.append(movie["title"])
            self.alianza_movies_loaded = True
