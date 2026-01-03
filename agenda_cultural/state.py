"""
Gestión del Estado de la Aplicación (App State).

Este módulo centraliza la lógica interactiva y el flujo de datos. Actúa como
puente entre la base de datos (Backend/DB) y la interfaz de usuario (Frontend),
definiendo las variables reactivas y los eventos de carga.
"""

import reflex as rx

from agenda_cultural.backend import Movie, get_task_logger
from agenda_cultural.shared import get_all_center_keys

db_logger = get_task_logger("database_core", "database.log")


class State(rx.State):
    movies: list[Movie] = []
    is_loading: bool = True

    @rx.event
    def load_movies(self):
        """Carga las películas desde la DB al iniciar la app."""
        try:
            with rx.session() as session:
                self.movies: list[Movie] = list(
                    session.exec(Movie.select().order_by(Movie.date)).all()
                )
        except Exception as e:
            db_logger.error(f"Error cargando las películas: {e}", exc_info=True)
            self.movies: list[Movie] = []

        finally:
            self.is_loading = False

    @rx.var
    def movies_by_center(self) -> dict[str, list[Movie]]:
        """
        Organiza las películas por centro cultural.
        Se recalcula automáticamente cuando self.movies cambia.
        """
        # Inicializamos con todas las keys para que el frontend no reciba undefined
        result: dict[str, list[Movie]] = {
            center_key: [] for center_key in get_all_center_keys()
        }

        for movie in self.movies:
            if movie.center in result:
                result[movie.center].append(movie)
        return result
