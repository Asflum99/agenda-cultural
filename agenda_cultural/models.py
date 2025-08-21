import reflex as rx
from datetime import datetime
from sqlalchemy import select

from agenda_cultural.cultural_centers import CULTURAL_CENTERS


class Movie(rx.Model, table=True):
    title: str
    location: str
    date: str
    center: str
    extracted_at: datetime = datetime.now()


class MoviesList(rx.State):
    movies: list[Movie] = []

    def load_movies(self):
        with rx.session() as session:
            result = session.exec(select(Movie)).scalars()
            self.movies = list(result)

    @rx.var
    def movies_by_center(self) -> dict[str, list[Movie]]:
        result = {center_key: [] for center_key in CULTURAL_CENTERS.keys()}

        for movie in self.movies:
            if movie.center in result:
                result[movie.center].append(movie)
        return result
