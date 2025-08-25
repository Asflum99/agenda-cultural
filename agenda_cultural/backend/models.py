import reflex as rx
from datetime import datetime
from sqlalchemy import DateTime, Column
from sqlmodel import Field


class Movie(rx.Model, table=True):
    title: str | None = None
    location: str | None = None
    date: datetime = Field(  # pyright: ignore[reportAny]
        sa_column=Column(DateTime(timezone=True))
    )
    center: str | None = None
    extracted_at: datetime = Field(  # pyright: ignore[reportAny]
        default_factory=datetime.now
    )
