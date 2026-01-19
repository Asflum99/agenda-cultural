import os

import reflex as rx
from dotenv import load_dotenv

load_dotenv()


api_url = os.getenv("API_URL", "http://localhost:8000")

config = rx.Config(
    app_name="agenda_cultural",
    # Asignamos la URL dinámica
    api_url=api_url,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    # Base de Datos
    db_url=os.getenv("DATABASE_URL"),
)
