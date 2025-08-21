import reflex as rx
import asyncio

from rxconfig import config
from agenda_cultural.pages.home import home
from agenda_cultural.scheduler import initialize_app
from agenda_cultural.models import Movie

rx.Model.create_all()

asyncio.run(initialize_app())

app = rx.App()


async def main():
    await initialize_app()
