import reflex as rx

from agenda_cultural.states.bnp.scraper import get_movies


class BnpState(rx.State):
    bnp_movies: list[dict] = []
    bnp_movies_loaded: bool = False

    @rx.event(background=True)
    async def load_movies(self):
        if self.bnp_movies_loaded:
            return
        if movies := await get_movies():
            async with self:
                self.bnp_movies.extend(movies)
                self.bnp_movies_loaded = True
