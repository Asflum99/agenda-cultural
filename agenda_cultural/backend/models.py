"""
Modelos de base de datos (ORM) para la app Agenda Cultural.

Define la estructura de las tablas y las entidades principales que se
utilizarán en la base de datos.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import reflex as rx
from sqlmodel import Field


def get_peruvian_time():
    """
    Obtiene la hora actual de Lima y le quita la información de zona horaria
    para que sea compatible con una base de datos Naive.
    """
    lima_time = datetime.now(ZoneInfo("America/Lima"))
    return lima_time.replace(tzinfo=None)


class Movie(rx.Model, table=True):  # ty: ignore[unsupported-base]
    """
    Representa una película en cartelera dentro de la base de datos.
    """

    # --- Campos Obligatorios ---
    # Título limpio de la película
    title: str

    # Dirección o nombre de la sala
    location: str

    # Fecha y hora del evento (Hora local Perú)
    date: datetime

    # Identificador/Slug del centro cultural (ej: "lum", "bnp", "af")
    center: str

    # --- Campos Opcionales ---
    # Dirección URL del póster de la película
    poster_url: str | None = None

    # URL original del evento
    source_url: str | None = None

    # --- Metadatos de Sistema ---
    # Hora de scrapeo
    extracted_at: datetime = Field(default_factory=get_peruvian_time)
