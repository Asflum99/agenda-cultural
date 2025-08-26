import locale
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright, Page
from agenda_cultural.backend.models import Movie


BNP = "https://eventos.bnp.gob.pe/externo/inicio"
MOVIE_BLOCK = ".no-padding.portfolio"
MOVIE_TITLE_PATTERN = r"(.+?)(\s\(\d+\))"


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
            _ = await page.goto(BNP, wait_until="load")

            initial_count = await page.locator(MOVIE_BLOCK).count()

            _ = await page.select_option("select#ContentPlaceHolder1_cboCategoria", "1")
            await page.locator("a#ContentPlaceHolder1_btnBuscarEventos").click()
            _ = await page.wait_for_function(
                f"""
                () => {{
                    const currentCount = document.querySelectorAll('{MOVIE_BLOCK}').length;
                    return currentCount !== {initial_count} && currentCount > 0;
                }}
                """
            )
            movies = await page.locator(MOVIE_BLOCK).count()

            movies_info: list[Movie] = []

            for movie in range(movies):
                if movie_info := await _get_movies_info(movie, page):
                    movies_info.append(movie_info)

            return movies_info

        except Exception as e:
            print(e)
            return []

        finally:
            await browser.close()


async def _get_movies_info(movie: int, page: Page):
    try:
        movie_obj = Movie()

        async with page.context.expect_page() as new_page_info:
            await page.locator(MOVIE_BLOCK).nth(movie).click()

        new_page = await new_page_info.value
        await new_page.wait_for_load_state("load")

        if title := await new_page.locator(
            "#ContentPlaceHolder1_gpCabecera h1"
        ).text_content():
            if match := re.match(MOVIE_TITLE_PATTERN, title):
                movie_obj.title = match.group(1)

        if date_time_element := await new_page.locator(
            "#ContentPlaceHolder1_gpDetalleEvento p:nth-child(2)"
        ).text_content():
            raw_date = date_time_element.strip()
            date = raw_date.replace("   ", " ")
            date = _transform_date_to_iso(date)
            movie_obj.date = date

        if location := await new_page.locator(
            "#ContentPlaceHolder1_gpUbicacion p"
        ).text_content():
            movie_obj.location = location

        movie_obj.center = "bnp"

        await new_page.close()

        return movie_obj

    except Exception as e:
        print(e)


def _transform_date_to_iso(date: str):
    _ = locale.setlocale(locale.LC_TIME, "es_PE.utf8")
    date = date[0].lower() + date[1:]
    date = _minus_month(date)
    new_date = datetime.strptime(date, "%A, %d de %B del %Y%l:%M%p")
    new_date = new_date.replace(tzinfo=ZoneInfo("America/Lima"))
    return new_date


def _minus_month(date: str):
    months = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    for month in months:
        if month in date:
            return date.replace(month, month.lower())
