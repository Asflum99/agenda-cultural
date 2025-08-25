# pyright: reportUnknownMemberType=false
import reflex as rx
from agenda_cultural.backend.models import Movie
from agenda_cultural.shared import get_all_center_keys


class MoviesList(rx.State):
    movies: list[Movie] = []

    @rx.event
    def load_movies(self):
        with rx.session() as session:
            result = session.exec(Movie.select()).all()
            self.movies = list(result)

    @rx.var
    def movies_by_center(self) -> dict[str, list[Movie]]:
        result: dict[str, list[Movie]] = {
            center_key: [] for center_key in get_all_center_keys()
        }
        for movie in self.movies:
            if movie.center in result:
                result[movie.center].append(movie)
        return result
