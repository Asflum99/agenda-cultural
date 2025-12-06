import reflex as rx


def navbar() -> rx.Component:
    return rx.hstack(
        rx.link(
            rx.heading("Agenda Cultural", size="5", weight="bold"),
            href="/",
            underline="none",
            color="inherit",
        ),
        rx.spacer(),
        # 2. ENLACES DE NAVEGACIÓN (A la derecha)
        rx.hstack(
            rx.link(
                rx.text("Cartelera", size="3", weight="medium"),
                href="/",
                underline="none",
                color=rx.color("gray", 11),
                _hover={"color": rx.color("blue", 9)},
            ),
            rx.link(
                rx.text("Acerca de", size="3", weight="medium"),
                href="/about",
                underline="none",
                color=rx.color("gray", 11),
                _hover={"color": rx.color("blue", 9)},
            ),
            spacing="5",
            align="center",
        ),
        # 3. ESTILOS DE LA BARRA FIJA
        position="sticky",
        top="0",
        z_index="999",
        padding_x=["1em", "1.5em", "2em"],
        padding_y="1em",
        width="100%",
        backdrop_filter="blur(10px)",
        background_color=rx.color("gray", 3, alpha=True),
        border_bottom=f"1px solid {rx.color('gray', 4)}",
        align="center",
    )
