import reflex as rx

from agenda_cultural.frontend.components import navbar


@rx.page(route="/about", title="Acerca de | Agenda Cultural")
def about() -> rx.Component:
    return rx.box(
        navbar(),
        rx.center(
            rx.vstack(
                # 1. Título y Descripción del Proyecto
                rx.heading("Agenda Cultural", size="8", text_align="center"),
                rx.text(
                    "Un proyecto open-source para centralizar la cartelera de cine cultural en Lima.",
                    font_size="1.2em",
                    text_align="center",
                    color=rx.color("gray", 11),
                ),
                rx.divider(width="100%"),
                # 2. SECCIÓN DE CRÉDITOS
                rx.vstack(
                    rx.text("Fuente de Datos", weight="bold", size="3"),
                    rx.image(
                        src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg",
                        width="150px",
                        alt="Logo de TMDB",
                    ),
                    rx.text(
                        "This product uses the TMDB API but is not endorsed or certified by TMDB.",
                        font_size="0.9em",
                        text_align="center",
                        color=rx.color("gray", 10),
                    ),
                    align="center",
                    spacing="3",
                    padding="2em",
                    border=f"1px solid {rx.color('gray', 4)}",
                    border_radius="12px",
                    width="100%",
                    bg=rx.color("gray", 2),
                ),
                # Estilos del Contenedor Principal
                spacing="6",
                align="center",
                width=["90%", "80%", "600px"],
                padding_y="4rem",
            ),
            width="100%",
            min_height="100vh",
        ),
    )
