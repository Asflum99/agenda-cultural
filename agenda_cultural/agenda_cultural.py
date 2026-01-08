"""
Punto de entrada principal de la aplicación Agenda Cultural.

Configura el estilo base, importa las páginas para registrarlas en el enrutador
e inicializa la instancia principal de la App.
"""

import reflex as rx

from rxconfig import config

from .backend.models import Movie
from .frontend.pages import about, home

BASE_STYLE: dict = {
    # Se fuerza este color oscuro para evitar, en algunos casos, el flasheo blanco al cargar la página
    "background_color": "#111113",
    "color": "white",
}

app = rx.App(
    style=BASE_STYLE,
    head_components=[
        rx.script(
            src="https://cloud.umami.is/script.js",
            custom_attrs={
                "data-website-id": "f82f1226-2565-4219-8a6a-aa25056d55df",
            },
            defer=True,
        )
    ],
)
