import reflex as rx
from datetime import datetime
from sqlalchemy import DateTime, Column
from sqlmodel import Field


class Movie(rx.Model, table=True):  # type: ignore[misc, call-arg]
    id: int = Field(default=None, primary_key=True)
    title: str
    location: str
    date: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    center: str
    extracted_at: datetime = Field(default_factory=datetime.now)
