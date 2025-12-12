import reflex as rx

from agenda_cultural.shared import get_all_center_keys, get_center_info
from agenda_cultural.state.state import State
from agenda_cultural.styles import NO_SCROLLBAR
from .movie_card import render_movie


def _render_cinema_row_base(center_key: str, is_mobile: bool) -> rx.Component:
    """Componente base compartido para renderizar una fila de cine."""
    movies_of_this_center = State.movies_by_center[center_key]
    center_info = get_center_info(center_key)

    return rx.cond(
        movies_of_this_center,
        rx.vstack(
            # 1. Título del Cine
            rx.heading(
                center_info["name"],
                size="5",
                color_scheme="gray",
                align_self="center",
                text_align="center",
            ),
            # 2. Carrusel Horizontal
            rx.hstack(
                rx.foreach(movies_of_this_center, render_movie),
                overflow_x="auto",
                width="100%",
                spacing="5",
                # --- DIFERENCIAS DE ESTILO (Móvil vs Desktop) ---
                # En móvil necesitamos padding lateral para que no pegue al borde.
                # En desktop suele alinearse con el contenedor principal.
                padding_x="4" if is_mobile else "0",
                padding_y="2" if is_mobile else "0",
                padding_bottom="0.5rem" if not is_mobile else "2",
                style=NO_SCROLLBAR,
                align_items="stretch",
            ),
            # Estilos del Contenedor
            width="100%",
            border_bottom=f"1px solid {rx.color('gray', 4)}",
            spacing="6",
            # --- DIFERENCIAS DE ESPACIADO ---
            # En móvil damos más aire abajo porque se usa el dedo.
            padding_bottom="1.5rem" if is_mobile else "1rem",
            margin_bottom="3.5rem" if is_mobile else "1rem",
        ),
    )


def _mobile_cinema_row(center_key: str) -> rx.Component:
    return _render_cinema_row_base(center_key, is_mobile=True)


def _desktop_cinema_row(center_key: str) -> rx.Component:
    return _render_cinema_row_base(center_key, is_mobile=False)


def mobile_feed_view() -> rx.Component:
    return rx.vstack(
        # Simplemente desempaquetamos la lista
        *[_mobile_cinema_row(key) for key in get_all_center_keys()],
        width="100%",
        spacing="0",
        display=["flex", "flex", "none", "none", "none"],
        padding_bottom="4rem",
        padding_top="2rem",
    )


def desktop_cinemas_view() -> rx.Component:
    return rx.vstack(
        # Iteramos sobre los cines activos
        *[_desktop_cinema_row(center_key) for center_key in get_all_center_keys()],
        width="100%",
        spacing="8",
        padding_y="2rem",
        align_items="start",
        display=["none", "none", "flex", "flex", "flex"],
    )
