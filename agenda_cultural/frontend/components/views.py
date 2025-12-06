import reflex as rx

from agenda_cultural.shared import get_all_center_keys, get_center_info
from agenda_cultural.state.state import State
from .movie_card import render_movie


def _accordion_item(center_key: str) -> rx.Component:
    center_info = get_center_info(center_key)
    movies = State.movies_by_center[center_key]

    # 1. ELIMINAMOS EL RX.COND EXTERNO
    # Devolvemos directamente el item para no romper la jerarquía
    return rx.accordion.item(
        rx.accordion.header(
            rx.accordion.trigger(
                rx.hstack(
                    rx.icon("clapperboard", size=18),
                    rx.text(center_info["name"], font_weight="bold"),
                    align="center",
                    spacing="2",
                    width="100%",
                ),
            ),
        ),
        rx.accordion.content(
            rx.vstack(
                rx.foreach(
                    movies,
                    render_movie,
                ),
                spacing="4",
                width="100%",
                align="center",
                padding_y="1em",
            )
        ),
        value=center_key,
        # 2. LA MAGIA AQUÍ:
        # Usamos la propiedad 'display' para ocultarlo si la lista 'movies' está vacía.
        # Si movies tiene datos (True) -> "block" (Visible)
        # Si movies está vacía (False) -> "none" (Oculto)
        display=rx.cond(movies, "block", "none"),
    )


def _desktop_column(center_key: str) -> rx.Component:
    center_info: dict[str, str] = get_center_info(center_key)
    movies = State.movies_by_center[center_key][:5]

    return rx.cond(
        movies,
        rx.vstack(
            rx.text(center_info["name"], font_weight="bold"),
            rx.foreach(
                movies,
                render_movie,
            ),
            align="center",
            spacing="4",
            min_width="0",
        ),
        rx.fragment(),
    )


def mobile_feed_view() -> rx.Component:
    """Retorna el acordeón completo con todos los cines"""
    return rx.accordion.root(
        *[_accordion_item(key) for key in get_all_center_keys()],
        type="multiple",
        collapsible=True,
        variant="outline",
        width="100%",
        display=["block", "block", "none", "none", "none"],
    )


def desktop_grid_view() -> rx.Component:
    return rx.grid(
        # Desempaquetamos las columnas igual que antes
        *[_desktop_column(key) for key in get_all_center_keys()],
        # --- CONFIGURACIÓN DE GRILLA ---
        columns="3",  # "Quiero exactamente 3 columnas siempre"
        spacing="5",  # "Quiero espacio 5 entre ellas SIEMPRE"
        width="100%",
        align_items="start",
        display=["none", "none", "grid", "grid", "grid"],
    )
