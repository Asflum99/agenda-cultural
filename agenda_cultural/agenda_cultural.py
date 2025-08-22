import reflex as rx
import asyncio

from rxconfig import config
from agenda_cultural.frontend.pages.home import home
from agenda_cultural.backend.app_initializer import initialize_app
from agenda_cultural.backend.models import Movie

rx.Model.create_all()

asyncio.run(initialize_app())

app = rx.App()


async def main():
    await initialize_app()
