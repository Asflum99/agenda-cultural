import reflex as rx

from rxconfig import config
from agenda_cultural.frontend.pages import home, about
from agenda_cultural.backend.models import Movies

BASE_STYLE: dict = {
    "background_color": "#111113",
    "color": "white",
}

app = rx.App(
    style=BASE_STYLE,
)
