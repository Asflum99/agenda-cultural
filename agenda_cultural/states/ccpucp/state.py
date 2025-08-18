import reflex as rx


class CcpucpState(rx.State):
    ccpucp_movies: list[str] = []
    ccpucp_movies_loaded: bool = False

    async def load_movies(self):
        pass
    
    