import reflex as rx

from agenda_cultural.backend.models import Movies


def render_movie(movie: Movies) -> rx.Component:
    return rx.card(
        # 1. SECCIÓN IMAGEN (Arriba y centrada)
        rx.inset(
            rx.center(
                rx.image(
                    src=movie.poster_url,
                    loading="lazy",
                    width="100%",
                    height="auto",
                    style={"aspect-ratio": "2/3"},
                    object_fit="cover",
                ),
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
            ),
            align="start",
            spacing="3",
            width="100%",
        ),
        # Estilos generales de la tarjeta
        width="100%",
        max_width="16rem",
        margin_x="auto",
        overflow="hidden",
    )
