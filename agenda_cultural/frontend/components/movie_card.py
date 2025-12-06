import reflex as rx

from agenda_cultural.backend.models import Movies


def render_movie(movie: Movies) -> rx.Component:
    return rx.card(
        # 1. SECCIÓN IMAGEN (Arriba y centrada)
        rx.inset(
            rx.center(
                rx.image(
                    src=movie.poster_url,
                    width="100%",  # Ocupa todo el ancho de la tarjeta
                    height="auto",
                    style={"aspect-ratio": "2/3"},  # Mantiene proporción de cine
                    object_fit="cover",
                ),
                width="100%",
                overflow="hidden",  # Evita que la imagen se salga
            ),
            side="top",  # Pega la imagen al borde superior de la tarjeta
            pb="current",  # Padding bottom automático
        ),
        # 2. SECCIÓN CONTENIDO (Abajo)
        rx.vstack(
            # Título destacado
            rx.heading(
                movie.title,
                size="4",
                weight="bold",
                margin_bottom="0.5em",
                color=rx.color("gray", 12),
            ),
            # Lista de datos (Solo para la info)
            rx.data_list.root(
                # Item Fecha
                rx.data_list.item(
                    rx.data_list.label(
                        rx.box(
                            "Fecha:",
                            width={"initial": "100%", "lg": "5rem"},
                            font_weight="bold",
                            text_transform="uppercase",
                            letter_spacing="0.05em",
                            font_size="0.75em",
                            color=rx.color("gray", 10),
                        ),
                    ),
                    rx.data_list.value(
                        rx.moment(
                            movie.date,
                            format="dddd D [de] MMMM - h:mm A",
                            locale="es",
                        ),
                        color=rx.color("gray", 11),
                        style={"text-transform": "capitalize"},
                    ),
                ),
                # Item Lugar
                rx.data_list.item(
                    rx.data_list.label(
                        rx.box(
                            "Lugar:",
                            width={"initial": "100%", "lg": "5rem"},
                            font_weight="bold",
                            text_transform="uppercase",
                            letter_spacing="0.05em",
                            font_size="0.75em",
                            color=rx.color("gray", 10),
                        ),
                    ),
                    rx.data_list.value(
                        rx.text(
                            movie.location,
                            color=rx.color("gray", 11),
                        ),
                        # Permite que el texto baje a la siguiente línea si es muy largo
                        style={"word-break": "break-word"},
                        width="100%",  # Que ocupe todo el espacio sobrante
                        align="end",  # Opcional: Alinear a la derecha se ve bien en data lists
                    ),
                ),
                size="1",
                width="100%",
                orientation={"initial": "vertical", "lg": "horizontal"},
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
        max_width="22rem",
        margin_x="auto",
        overflow="hidden",
    )
