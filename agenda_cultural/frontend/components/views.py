import reflex as rx

from agenda_cultural.shared import get_all_center_keys, get_center_info
from agenda_cultural.state.state import State
from agenda_cultural.styles import NO_SCROLLBAR
from .movie_card import render_movie


def _accordion_item(center_key: str) -> rx.Component:
    center_info = get_center_info(center_key)
    movies = State.movies_by_center[center_key]

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
        # Si movies tiene datos (True) -> "block" (Visible)
        # Si movies está vacía (False) -> "none" (Oculto)
        display=rx.cond(movies, "block", "none"),
    )


def _cinema_row(center_key: str) -> rx.Component:
    movies_of_this_center = State.movies_by_center[center_key]
    center_info = get_center_info(center_key)
    pretty_name = center_info.get("name", center_key.title())

    return rx.cond(
        # Si la lista está vacía, no renderiza nada (ni el título).
        movies_of_this_center,
        rx.vstack(
            # 1. Título del Cine
            rx.heading(
                pretty_name,
                size="5",
                margin_bottom="4",
                color_scheme="gray",
                align_self="center",
            ),
            # 2. El Carrusel Horizontal
            rx.hstack(
                rx.foreach(movies_of_this_center, render_movie),
                # Estilos de Scroll Horizontal
                overflow_x="auto",
                width="100%",
                spacing="4",
                padding_bottom="0.5rem",
                style=NO_SCROLLBAR,
                align_items="stretch",
            ),
            width="100%",
            align_items="start",
            bg=rx.color("gray", 2),
            border=f"1px solid {rx.color('gray', 4)}",
            border_radius="12px",
            padding="1.5rem",
            gap="2rem",
        ),
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


def desktop_cinemas_view() -> rx.Component:
    return rx.vstack(
        # Generamos una fila por cada cine conocido
        *[_cinema_row(center_key) for center_key in get_all_center_keys()],
        width="100%",
        spacing="8",
        padding_y="2rem",
        align_items="start",
        display=["none", "none", "flex", "flex", "flex"],
    )
