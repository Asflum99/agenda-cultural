import reflex as rx
from agenda_cultural.states.state_orchestrator import EventsState
from agenda_cultural.states.alianza_francesa_state import AlianzaFrancesaState
from agenda_cultural.states.bnp_state import BnpState
from agenda_cultural.states.ccpucp_state import CcpucpState


@rx.page("/", on_load=EventsState.load_all_events)
def home() -> rx.Component:
    return rx.vstack(
        rx.heading("Agenda Cultural", size="9"),
        rx.hstack(
            rx.vstack(
                "Alianza Francesa",
                rx.cond(
                    AlianzaFrancesaState.alianza_movies_loaded,
                    rx.foreach(
                        AlianzaFrancesaState.alianza_movies,
                        lambda movie: rx.text(movie),
                    ),
                    rx.text("Cargando1..."),
                ),
                align="center",
            ),
            rx.vstack(
                "CCPUCP",
                rx.cond(
                    BnpState.bnp_movies_loaded,
                    rx.foreach(BnpState.bnp_movies, lambda movie: rx.text(movie)),
                    rx.text("Cargando2..."),
                ),
                align="center",
            ),
            rx.vstack(
                "Biblioteca Nacional del Perú",
                rx.cond(
                    CcpucpState.bnp_movies_loaded,
                    rx.foreach(CcpucpState.bnp_movies, lambda movie: rx.text(movie)),
                    rx.text("Cargando3..."),
                ),
                align="center",
            ),
            justify="between",
            width="70%",
        ),
        spacing="9",
        align="center",
        padding_top="12rem",
    )
