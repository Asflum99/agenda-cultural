import reflex as rx
from agenda_cultural.states.alianza_francesa.state import AlianzaFrancesaState
from agenda_cultural.states.bnp.state import BnpState
from agenda_cultural.states.ccpucp.state import CcpucpState


class MovieState(rx.State):
    def load_all_movies(self):
        """Disparar tareas en paralelo"""
        return [
            AlianzaFrancesaState.load_movies,
            BnpState.load_movies,
            CcpucpState.load_movies,
        ]
