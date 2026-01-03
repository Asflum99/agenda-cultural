"""
Punto de entrada principal de la aplicación Agenda Cultural.

Configura el estilo base, importa las páginas para registrarlas en el enrutador
e inicializa la instancia principal de la App.
"""

import reflex as rx

from rxconfig import config
from .frontend.pages import home, about
from .backend.models import Movie

BASE_STYLE: dict = {
    # Se fuerza este color oscuro para evitar, en algunos casos, el flasheo blanco al cargar la página
    "background_color": "#111113",
    "color": "white",
}

app = rx.App(
    style=BASE_STYLE,
)
