import reflex as rx
import os
from dotenv import load_dotenv

load_dotenv()


if os.getenv("REFLEX_ENV") == "prod":
    # CONFIGURACIÓN PARA AWS
    my_api_url = "https://agendacultural.duckdns.org"
else:
    # CONFIGURACIÓN PARA LOCAL
    my_api_url = "http://localhost:8000"

config = rx.Config(
    app_name="agenda_cultural",
    # Asignamos la URL dinámica
    api_url=my_api_url,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    # Base de Datos
    db_url=os.getenv("DATABASE_URL"),
)
