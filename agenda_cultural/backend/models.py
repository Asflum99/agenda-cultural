import reflex as rx
from datetime import datetime


class Movie(rx.Model, table=True):
    title: str
    location: str
    date: str
    center: str
    extracted_at: datetime = datetime.now()
