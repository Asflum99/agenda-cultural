"""
Punto de entrada principal de la aplicación Agenda Cultural.

Configura el estilo base, importa las páginas para registrarlas en el enrutador
e inicializa la instancia principal de la App.
"""

import os

import reflex as rx
from dotenv import load_dotenv

from rxconfig import config

from .backend.models import Movie
from .frontend.pages import about, home

# Carga variables de entorno para saber si está en producción o local
load_dotenv()


BASE_STYLE: dict = {
    # Se fuerza este color oscuro para evitar, en algunos casos, el flasheo blanco al cargar la página
    "background_color": "#111113",
    "color": "white",
}

# Lógica para que Umami solo se ejecute en producción y no en local
IS_PROD = os.getenv("REFLEX_ENV") == "prod"
UMAMI_ID = os.getenv("UMAMI_WEBSITE_ID")

head_comps = []

if IS_PROD and UMAMI_ID:
    head_comps.append(
        rx.script(
            src="https://cloud.umami.is/script.js",
            custom_attrs={
                "data-website-id": "f82f1226-2565-4219-8a6a-aa25056d55df",
            },
            defer=True,
        )
    )

app = rx.App(
    style=BASE_STYLE,
    head_components=head_comps,
)
