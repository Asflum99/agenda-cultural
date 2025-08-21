import reflex as rx
import os

from dotenv import load_dotenv

load_dotenv()


config = rx.Config(
    app_name="agenda_cultural",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    db_url=os.getenv("DATABASE_URL"),
)
