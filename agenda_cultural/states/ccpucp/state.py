import reflex as rx

from agenda_cultural.states.ccpucp.scraper import get_movies


class CcpucpState(rx.State):
    ccpucp_movies: list[dict] = []
    ccpucp_movies_loaded: bool = False

    @rx.event(background=True)
    async def load_movies(self):
        if self.ccpucp_movies_loaded:
            return
        if movies := await get_movies():
            async with self:
                self.ccpucp_movies.extend(movies)
                self.ccpucp_movies_loaded = True
