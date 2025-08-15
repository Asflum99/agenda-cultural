import reflex as rx

config = rx.Config(
    app_name="agenda_cultural",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)