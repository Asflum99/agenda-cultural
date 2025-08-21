import reflex as rx
from agenda_cultural.components.movie_components import movie_section
from agenda_cultural.models import MoviesList
from agenda_cultural.cultural_centers import CULTURAL_CENTERS


@rx.page("/", "Agenda cultural", on_load=MoviesList.load_movies)
def home() -> rx.Component:
    return rx.vstack(
        rx.heading("Agenda Cultural", size="9"),
        rx.hstack(
            *[movie_section(center_key) for center_key in CULTURAL_CENTERS.keys()],
            justify="between",
            width="70%",
        ),
        spacing="9",
        align="center",
        padding_top="12rem",
    )
