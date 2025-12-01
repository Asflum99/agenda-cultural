import reflex as rx
from agenda_cultural.backend.models import Movies
from agenda_cultural.shared import get_all_center_keys


class State(rx.State):
    movies: list[Movies] = []

    @rx.event
    def load_movies(self):
        with rx.session() as session:
            self.movies = list(
                session.exec(
                    Movies.select().order_by(
                        Movies.date  # pyright: ignore [reportArgumentType]
                    )
                ).all()
            )

    @rx.var
    def movies_by_center(self) -> dict[str, list[Movies]]:
        result: dict[str, list[Movies]] = {
            center_key: [] for center_key in get_all_center_keys()
        }
        for movie in self.movies:
            if movie.center in result:
                result[movie.center].append(movie)
        return result
