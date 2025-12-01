# pyright: reportUnknownMemberType=false
import reflex as rx
from agenda_cultural.frontend.components import movie_section
from agenda_cultural.state.state import State
from agenda_cultural.shared import get_all_center_keys


@rx.page("/", "Agenda cultural", on_load=State.load_movies)
def home() -> rx.Component:
    return rx.vstack(
        rx.heading("Agenda Cultural", size="9"),
        rx.hstack(
            *[movie_section(center_key) for center_key in get_all_center_keys()],
            justify="between",
            width="70%",
        ),
        spacing="9",
        align="center",
        padding_top="12rem",
    )
