import reflex as rx

from agenda_cultural.backend.models import Movie
from agenda_cultural.frontend.state.movie_state import MoviesList
from agenda_cultural.shared import get_center_info


def render_movie(movie: Movie) -> rx.Component:
    return rx.card(
        rx.data_list.root(
            rx.data_list.item(
                rx.data_list.label("Película:"),
                rx.data_list.value(
                    rx.text(
                        movie.title,
                        font_weight="bold",
                    )
                ),
                align="center",
                style={"gap": "2px"},
            ),
            rx.data_list.item(
                rx.data_list.label("Fecha:"),
                rx.data_list.value(
                    rx.moment(  # type: ignore[operator]
                        movie.date,
                        format="dddd D [de] MMMM - h:mm A",
                        locale="es",
                    ),
                    font_weight="bold",
                    style={"text-transform": "capitalize"},  # Considerar si usarlo o no
                ),
                style={"gap": "2px"},
            ),
            rx.data_list.item(
                rx.data_list.label("Lugar"),
                rx.data_list.value(rx.text(movie.location, font_weight="bold")),
                style={"gap": "2px"},
            ),
        ),
        width="25rem",
        style={"word-wrap": "break-word", "overflow": "hidden"},
    )


def movie_section(center_key: str) -> rx.Component:
    center_info = get_center_info(center_key)
    return rx.vstack(
        rx.text(center_info["name"], font_weight="bold"),
        rx.foreach(
            MoviesList.movies_by_center[center_key][:5],
            render_movie,
        ),
        align="center",
    )
