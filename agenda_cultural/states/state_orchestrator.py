import reflex as rx
from agenda_cultural.states.alianza_francesa_state import AlianzaFrancesaState
from agenda_cultural.states.bnp_state import BnpState
from agenda_cultural.states.ccpucp_state import CcpucpState


class EventsState(rx.State):
    # Sin datos propios, solo coordinación
    async def load_all_events(self):
        # Podrías hacerlo en paralelo después
        await AlianzaFrancesaState.load_movies()
        await CcpucpState.load_movies() 
        await BnpState.load_movies()
