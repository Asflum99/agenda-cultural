import reflex as rx
from datetime import datetime
from sqlmodel import Field
from zoneinfo import ZoneInfo

def get_peruvian_time():
    """
    Obtiene la hora actual de Lima y le quita la información de zona horaria
    para que sea compatible con una base de datos Naive.
    """
    lima_time = datetime.now(ZoneInfo("America/Lima"))
    return lima_time.replace(tzinfo=None)

class Movies(rx.Model, table=True):
    title: str | None = None
    location: str | None = None
    date: datetime | None = None 
    center: str | None = None
    extracted_at: datetime = Field(
        default_factory=get_peruvian_time
    )
