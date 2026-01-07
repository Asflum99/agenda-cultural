import reflex as rx

from agenda_cultural.backend import Movie


def render_movie_poster(movie: Movie):
    """
    Renderizar el póster si existen.
    Caso contrario, utiliza un placeholder.
    """
    return rx.cond(
        movie.poster_url,
        rx.image(
            src=movie.poster_url,
            loading="lazy",
            width="100%",
            height="auto",
            style={"aspect-ratio": "2/3"},
            object_fit="cover",
        ),
        rx.center(
            rx.vstack(
                rx.text("( ✖ _ ✖ )", font_size="2em", color="#ddd"),
                rx.text("Se busca", font_weight="bold", color="#ddd"),
                rx.text(
                    "Póster no encontrado",
                    font_size="0.85em",
                    opacity=0.7,
                    color="#ddd",
                ),
                spacing="2",
                align_items="center",
            ),
            width="100%",
            height="100%",
            background_color="#1a1a1a",
            border="2px dashed #333",
            padding="1em",
            color="#666",
            style={"aspect-ratio": "2/3"},
        ),
    )


def render_movie(movie: Movie) -> rx.Component:
    return rx.card(
        # 1. SECCIÓN IMAGEN (Arriba y centrada)
        rx.inset(
            rx.center(
                render_movie_poster(movie),
                width="100%",
                overflow="hidden",
            ),
            side="top",
            pb="current",
        ),
        # 2. SECCIÓN CONTENIDO (Abajo)
        rx.vstack(
            # Título destacado
            rx.heading(
                movie.title,
                size="3",
                weight="bold",
                margin_bottom="0.25em",
                color=rx.color("gray", 12),
            ),
            # Lista de datos
            rx.data_list.root(
                # Item Fecha
                rx.data_list.item(
                    rx.data_list.label(
                        rx.box(
                            "Fecha:",
                            font_weight="bold",
                            text_transform="uppercase",
                            letter_spacing="0.05em",
                            font_size="0.75em",
                            color=rx.color("gray", 10),
                        ),
                        width="100%",
                    ),
                    rx.data_list.value(
                        rx.moment(
                            movie.date,
                            format="dddd D [de] MMMM - h:mm A",
                            locale="es",
                        ),
                        color=rx.color("gray", 11),
                        style={"text-transform": "capitalize"},
                        width="100%",
                        align="start",
                    ),
                    spacing="1",
                ),
                # Item Lugar
                rx.data_list.item(
                    rx.data_list.label(
                        rx.box(
                            "Lugar:",
                            font_weight="bold",
                            text_transform="uppercase",
                            letter_spacing="0.05em",
                            font_size="0.75em",
                            color=rx.color("gray", 10),
                        ),
                        width="100%",
                    ),
                    rx.data_list.value(
                        rx.text(
                            movie.location,
                            color=rx.color("gray", 11),
                        ),
                        style={"word-break": "break-word"},
                        width="100%",
                        align="start",
                    ),
                    spacing="1",
                ),
                size="1",
                width="100%",
                orientation="vertical",
                spacing="3",
            ),
            rx.box(
                rx.link(
                    "Ver sitio oficial",
                    href=rx.cond(movie.source_url, movie.source_url, "#"),
                    is_external=True,
                ),
                width="100%",
                display="flex",
                justify_content="center",
                padding_top="1rem",
                margin_top="auto",
            ),
            align="start",
            spacing="3",
            width="100%",
            flex_grow="1",
        ),
        # Estilos generales de la tarjeta
        width="100%",
        max_width="16rem",
        min_width="15rem",
        margin_x="auto",
        overflow="hidden",
        display="flex",
        flex_direction="column",
    )
