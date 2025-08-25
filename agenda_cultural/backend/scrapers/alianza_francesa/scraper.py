import locale
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright, Page
from datetime import datetime
from agenda_cultural.backend.models import Movie


ALIANZA_FRANCESA = (
    "https://aflima.org.pe/eventos/?post_type=evento&categoria%5B%5D=cine"
)


async def get_movies() -> list[Movie]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
            ],
        )
        page = await browser.new_page()

        try:
            _ = await page.goto(ALIANZA_FRANCESA, wait_until="domcontentloaded")

            # Grupo de secciones que proyectan películas gratuitas
            cine_locators = await page.locator(
                ".ctbtn", has_text="Ingreso libre"
            ).count()

            movies_info: list[Movie] = []

            for locator in range(cine_locators):
                await _enter_movie_page(locator, page)

                movies = await page.locator(".cajas_cont_item").count()

                for movie in range(movies):
                    if movie_info := await _get_movies_info(movie, page):
                        movies_info.append(movie_info)

                _ = await page.go_back(wait_until="domcontentloaded")

            return _order_movies(movies_info)

        except Exception as e:
            print(e)
            return []

        finally:
            await browser.close()


async def _get_movies_info(movie: int, page: Page):
    try:
        movie_obj = Movie()
        movie_box = page.locator(".cajas_cont_item").nth(movie)

        if raw_title := await movie_box.locator(
            ".cajas_cont_item_fecha .cajas__fecha_txt"
        ).text_content():
            movie_obj.title = raw_title.replace("\n", " ").strip()

        blocks = await movie_box.locator(
            ".cajas_cont_item_info .cajas__info_fecha2"
        ).count()

        keys = ["date", "location"]
        for block in range(blocks):
            if (
                raw_info := await movie_box.locator(
                    ".cajas_cont_item_info .cajas__info_fecha2"
                )
                .nth(block)
                .text_content()
            ):
                info = raw_info.replace("\n", " ").strip()

                if keys[block] == "date":
                    info = _transform_date_to_iso(info)
                    movie_obj.date = info
                else:
                    movie_obj.location = info

        movie_obj.center = "alianza francesa"

        return movie_obj
    except Exception as e:
        print(e)


async def _enter_movie_page(locator: int, page: Page):
    await page.locator(".ctbtn a.btn-outline-primary").nth(locator).click()
    await page.wait_for_load_state("domcontentloaded")


def _transform_date_to_iso(date: str):
    _ = locale.setlocale(locale.LC_TIME, "es_PE.utf8")
    raw_date = date[0].lower() + date[1:]  # Transformar la primera letra en minúscula
    raw_date = raw_date.replace("pm.", "PM").replace("am.", "AM")
    raw_date = raw_date + " 2025"

    formats_to_try = [
        "%A%e de %B, %I:%M %p %Y",  # Para días con un dígito
        "%A %d de %B, %I:%M %p %Y",  # Para días con dos dígitos
    ]

    for fmt in formats_to_try:
        try:
            new_date = datetime.strptime(raw_date, fmt)
            new_date = new_date.replace(tzinfo=ZoneInfo("America/Lima"))
            return new_date
        except ValueError:
            continue

    raise ValueError(f"No se pudo parsear la fecha: {raw_date}")


def _order_movies(
    movies: list[Movie],
) -> list[Movie]:
    """Ordena las películas por fecha de proyección"""
    return sorted(movies, key=lambda movie: Movie.date)
