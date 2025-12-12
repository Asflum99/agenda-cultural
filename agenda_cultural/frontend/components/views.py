import reflex as rx

from agenda_cultural.shared import get_all_center_keys, get_center_info
from agenda_cultural.state.state import State
from agenda_cultural.styles import NO_SCROLLBAR
from .movie_card import render_movie


def _mobile_cinema_row(center_key: str) -> rx.Component:
    """Una fila de cine simplificada para móvil (sin la caja gris grande)"""
    movies_of_this_center = State.movies_by_center[center_key]
    center_info = get_center_info(center_key)

    return rx.cond(
        movies_of_this_center,
        rx.vstack(
            # 1. Título del Cine
            rx.heading(
                center_info["name"],
                size="5",
                margin_bottom="4",
                color_scheme="gray",
                align_self="center",
            ),
            # 2. Carrusel Horizontal (Igual que desktop pero ajustado)
            rx.hstack(
                rx.foreach(movies_of_this_center, render_movie),
                overflow_x="auto",
                width="100%",
                spacing="3",
                padding_bottom="0.5rem",
                style=NO_SCROLLBAR,
                align_items="stretch",
            ),
            width="100%",
            border_bottom=f"1px solid {rx.color('gray', 4)}",
            padding_bottom="1.5rem",
            margin_bottom="3.5rem",
        ),
    )


def _desktop_cinema_row(center_key: str) -> rx.Component:
    movies_of_this_center = State.movies_by_center[center_key]
    center_info = get_center_info(center_key)

    return rx.cond(
        movies_of_this_center,
        rx.vstack(
            # 1. Título del Cine
            rx.heading(
                center_info["name"],
                size="5",
                margin_bottom="4",
                color_scheme="gray",
                align_self="center",
            ),
            # 2. El Carrusel Horizontal
            rx.hstack(
                rx.foreach(movies_of_this_center, render_movie),
                overflow_x="auto",
                width="100%",
                spacing="3",
                padding_bottom="0.5rem",
                style=NO_SCROLLBAR,
                align_items="stretch",
            ),
            width="100%",
            border_bottom=f"1px solid {rx.color('gray', 4)}",
            padding_bottom="1.5rem",
            margin_bottom="1.5rem",
        ),
    )


def mobile_feed_view() -> rx.Component:
    return rx.vstack(
        # Simplemente desempaquetamos la lista
        *[_mobile_cinema_row(key) for key in get_all_center_keys()],
        width="100%",
        spacing="0",
        display=["flex", "flex", "none", "none", "none"],
        padding_bottom="4rem",
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
