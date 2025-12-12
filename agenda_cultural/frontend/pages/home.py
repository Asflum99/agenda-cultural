import reflex as rx
from agenda_cultural.state.state import State
from agenda_cultural.frontend.components import (
    mobile_feed_view,
    desktop_cinemas_view,
    navbar,
)


@rx.page("/", "Agenda cultural", on_load=State.load_movies)
def home() -> rx.Component:
    return rx.box(
        navbar(),
        rx.cond(
            State.is_loading,
            # --- OPCIÓN A: MIENTRAS CARGA ---
            rx.center(
                rx.vstack(
                    rx.spinner(size="3", color="gray"),
                    rx.text("Buscando eventos...", color="gray"),
                    align="center",
                    spacing="4",
                ),
                width="100%",
                min_height="50vh",
                padding_y="4rem",
            ),
            # --- OPCIÓN B: CUANDO YA HAY DATOS ---
            rx.vstack(
                mobile_feed_view(),
                desktop_cinemas_view(),
                width=["95%", "90%", "85%", "70%"],
                margin_x="auto",
                align="center",
                spacing="6",
            ),
        ),
    )
