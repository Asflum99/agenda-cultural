import reflex as rx
from agenda_cultural.state.state import State
from agenda_cultural.frontend.components import mobile_feed_view, desktop_grid_view


@rx.page("/", "Agenda cultural", on_load=State.load_movies)
def home() -> rx.Component:
    return rx.vstack(
        rx.heading("Agenda Cultural", size="8", text_align="center"),
        mobile_feed_view(),
        desktop_grid_view(),
        rx.divider(),
        # Anchos para Móvil (Celular y tablet) y Escritorio (Laptop, Monitor normal/monitor ancho)
        width=["95%", "90%", "85%", "70%"],
        margin_x="auto",
        align="center",
        spacing="6",
        padding_y="4rem",
    )
