"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from rxconfig import config


class State(rx.State):
    """The app state."""


def index() -> rx.Component:
    # Welcome Page
    return rx.vstack(
        rx.heading("Agenda Cultural", size="9"),
        rx.hstack(
            rx.vstack("Alianza Francesa", rx.text("Película 1"), align="center"),
            rx.vstack("CCPUCP", rx.text("Película 1"), align="center"),
            rx.vstack(
                "Biblioteca Nacional del Perú", rx.text("Película 1"), align="center"
            ),
            justify="between",
            width="70%",
        ),
        spacing="9",
        align="center",
        padding_top="12rem",
    )


app = rx.App()
app.add_page(index)
