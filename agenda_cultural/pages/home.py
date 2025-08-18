import reflex as rx
from agenda_cultural.states.movie_loader import MovieState
from agenda_cultural.states.alianza_francesa.state import AlianzaFrancesaState
from agenda_cultural.states.bnp.state import BnpState
from agenda_cultural.states.ccpucp.state import CcpucpState
from agenda_cultural.components.movie_components import movie_section


@rx.page("/", on_load=MovieState.load_all_movies)
def home() -> rx.Component:
    return rx.vstack(
        rx.heading("Agenda Cultural", size="9"),
        rx.hstack(
            movie_section(
                "Alianza Francesa",
                AlianzaFrancesaState.alianza_movies_loaded,
                AlianzaFrancesaState.alianza_movies,
            ),
            # movie_section(
            #     "CCPUCP",
            #     CcpucpState.ccpucp_movies_loaded,
            #     CcpucpState.ccpucp_movies,
            # ),
            # movie_section(
            #     "Biblioteca Nacional del Perú",
            #     BnpState.bnp_movies_loaded,
            #     BnpState.bnp_movies,
            # ),
            justify="between",
            width="70%",
        ),
        spacing="9",
        align="center",
        padding_top="12rem",
    )
