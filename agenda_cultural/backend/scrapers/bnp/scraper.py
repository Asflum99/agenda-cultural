import locale
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright, Page


BNP = "https://eventos.bnp.gob.pe/externo/inicio"
MOVIE_BLOCK = ".no-padding.portfolio"


async def get_movies():
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
            await page.goto(BNP, wait_until="load")

            initial_count = await page.locator(MOVIE_BLOCK).count()

            await page.select_option("select#ContentPlaceHolder1_cboCategoria", "1")
            await page.locator("a#ContentPlaceHolder1_btnBuscarEventos").click()
            await page.wait_for_function(
                f"""
                () => {{
                    const currentCount = document.querySelectorAll('{MOVIE_BLOCK}').length;
                    return currentCount !== {initial_count} && currentCount > 0;
                }}
                """
            )
            movies = await page.locator(MOVIE_BLOCK).count()

            movies_info: list[dict] = []

            for movie in range(movies):
                movie_info = await _get_movies_info(movie, page)
                movies_info.append(movie_info)

            return movies_info

        except Exception as e:
            print(e)
        finally:
            await browser.close()


async def _get_movies_info(movie: int, page: Page):
    try:
        movie_info = {}

        async with page.context.expect_page() as new_page_info:
            await page.locator(MOVIE_BLOCK).nth(movie).click()

        new_page = await new_page_info.value
        await new_page.wait_for_load_state("load")

        movie_info["title"] = await new_page.locator(
            "#ContentPlaceHolder1_gpCabecera h1"
        ).text_content()
        date_time_element = await new_page.locator(
            "#ContentPlaceHolder1_gpDetalleEvento p:nth-child(2)"
        ).text_content()

        if raw_date := date_time_element.strip():
            date = raw_date.replace("   ", " ")

        date = _transform_date_to_iso(date)

        movie_info["date"] = date

        movie_info["location"] = await new_page.locator(
            "#ContentPlaceHolder1_gpUbicacion p"
        ).text_content()

        movie_info["center"] = "bnp"

        await new_page.close()

        return movie_info

    except Exception as e:
        print(e)


def _transform_date_to_iso(date: str):
    locale.setlocale(locale.LC_TIME, "es_PE.utf8")
    date = date[0].lower() + date[1:]
    date = _minus_month(date)
    new_date = datetime.strptime(date, "%A, %d de %B del %Y%l:%M%p")
    new_date = new_date.replace(tzinfo=ZoneInfo("America/Lima"))
    return new_date.isoformat()


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
