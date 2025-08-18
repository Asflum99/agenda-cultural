import reflex as rx


def render_movie(movie: dict) -> rx.Component:
    return rx.card(
        rx.data_list.root(
            rx.data_list.item(
                rx.data_list.label("Película:"),
                rx.data_list.value(
                    rx.text(
                        movie["title"],
                        font_weight="bold",
                    )
                ),
                align="center",
                style={"gap": "2px"},
            ),
            rx.data_list.item(
                rx.data_list.label("Fecha:"),
                rx.data_list.value(rx.text(movie["date"], font_weight="bold")),
                style={"gap": "2px"},
            ),
            rx.data_list.item(
                rx.data_list.label("Lugar"),
                rx.data_list.value(rx.text(movie["location"], font_weight="bold")),
                style={"gap": "2px"},
            ),
        ),
        width="25rem",
        style={"word-wrap": "break-word", "overflow": "hidden"},
    )


def movie_section(title: str, movies_loaded: bool, movies: list[dict]) -> rx.Component:
    return rx.vstack(
        rx.text(title, font_weight="bold"),
        rx.cond(
            movies_loaded,
            rx.foreach(movies[:5], render_movie),
            rx.text("Cargando..."),
        ),
        align="center",
    )
