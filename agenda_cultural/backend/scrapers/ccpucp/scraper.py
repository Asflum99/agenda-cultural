import re
from datetime import datetime
import locale
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright, Page
from agenda_cultural.backend.models import Movie

CCPUCP = "https://centrocultural.pucp.edu.pe/cine.html"
MOVIE_TITLE_SELECTOR = ".catItemTitle a"


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
            _ = await page.goto(CCPUCP, wait_until="load")

            await page.locator("a.subCategoryImage").click()
            await page.wait_for_load_state("load")
            movies = await page.locator(MOVIE_TITLE_SELECTOR).count()

            movies_info: list[Movie] = []

            for movie in range(movies):
                if movie_info := await _get_movies_info(movie, page):
                    movies_info.append(movie_info)
                _ = await page.go_back(wait_until="load")

            return movies_info

        except Exception as e:
            print(e)
            return []

        finally:
            await browser.close()


async def _get_movies_info(movie: int, page: Page):
    try:
        movie_obj = Movie()

        movie_title = await page.locator(MOVIE_TITLE_SELECTOR).nth(movie).inner_text()
        await page.locator(MOVIE_TITLE_SELECTOR).nth(movie).click()
        await page.wait_for_load_state("load")
        fecha_locator = page.locator(
            'p:has(span strong:text("FUNCIONES")) span'
        ).filter(
            has_text=re.compile(
                r"(lunes|martes|miércoles|jueves|viernes|sábado|domingo)\s+\d{1,2}\s+de\s+\w+"
            )
        )
        if date_exist := await fecha_locator.text_content():
            _ = locale.setlocale(locale.LC_TIME, "es_PE.utf8")
            date = date_exist.split("|")[0].strip() + " 2025"
            date_object = datetime.strptime(date, "%A %d de %B %Y")
            now = datetime.now()

            if date_object > now:
                date_exist = _transform_date_to_iso(date_exist)
                movie_obj.date = date_exist
                movie_obj.title = _clean_title(movie_title)
                movie_obj.location = "Av. Camino Real 1075, San Isidro"
                movie_obj.center = "ccpucp"

                return movie_obj
            else:
                return None
        else:
            return None

    except Exception as e:
        print(e)


def _transform_date_to_iso(date: str):
    date = date.strip().replace("a.m.", "AM 2025").replace("p.m.", "PM 2025")
    new_date = datetime.strptime(date, "%A %d de %B | %I:%M %p %Y")
    new_date = new_date.replace(tzinfo=ZoneInfo("America/Lima"))
    return new_date


def _clean_title(movie_title: str):
    movie = movie_title.lower()
    movie_words = movie.split()
    movie_words[0] = movie_words[0].capitalize()
    return " ".join(movie_words)