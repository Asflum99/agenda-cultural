import re
from typing import override
from playwright.async_api import async_playwright, Page
from agenda_cultural.backend.models import Movies
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.services.tmdb_service import get_movie_poster
from agenda_cultural.backend.constants import MAPA_MESES

LUM = "https://lum.cultura.pe/actividades"
EVENT_BLOCK_SELECTOR = ".views-row"
TITLE_PATTERN = re.compile(r'[“"]([^”"]+)[”"]')
MOVIE_TITLE_SELECTOR = ".field-item p strong"
DATE_PATTERN = re.compile(
    r"(?i)(lunes|martes|miércoles|jueves|viernes|sábado|domingo)\s+(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"
)
TIME_PATTERN = re.compile(r"(?i)(\d{1,2}:\d{2})\s*(a\.?|p\.?)\s*m\.?")


class LumScraper(ScraperInterface):
    @override
    async def get_movies(self):
        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                _ = await page.goto(LUM, wait_until="load")

                events_block = await page.locator(EVENT_BLOCK_SELECTOR).count()

                movies_info: list[Movies] = []

                for event in range(events_block):
                    event_title = (
                        await page.locator(EVENT_BLOCK_SELECTOR)
                        .nth(event)
                        .locator(".views-field-title")
                        .inner_text()
                    ).lower()

                    if match := re.compile(
                        r"agenda\s+([a-zA-Z]+)\s+(\d{4})", re.IGNORECASE
                    ).search(event_title):
                        month = match.group(1).lower()

                        month_num = MAPA_MESES.get(month)

                        if month_num:
                            await page.locator(EVENT_BLOCK_SELECTOR).nth(event).click()
                            await page.wait_for_load_state("load")
                            if movies := await self._get_movies_info(page):
                                movies_info.extend(movies)
                                break

                return movies_info

            except Exception as e:
                print(e)
                return [Movies()]

            finally:
                await browser.close()

    async def _get_movies_info(self, page: Page):
        paragraph_selector = ".field-item p"
        paragraphs = await page.locator(paragraph_selector).all()
        movies_to_return: list[Movies] = []

        for p_locator in paragraphs:
            full_text = await p_locator.inner_text()

            if "cine" not in full_text.lower():
                continue

            movie_obj = Movies()

            lines = full_text.split("\n")

            day = 0
            month = ""
            time = ""

            for line in lines:
                line = line.strip()

                if "“" in line or '"' in line:
                    movie_title = self._clean_title(line)
                    movie_obj.title = movie_title
                    movie_obj.poster_url = get_movie_poster(movie_title)

                if match_date := DATE_PATTERN.search(line):
                    raw_date = match_date.group()
                    day = int(raw_date.split()[1])
                    month = raw_date.split()[3]

                if match_time := TIME_PATTERN.search(line):
                    time = match_time.group()
                else:
                    continue

                if movie_date := self.validate_and_build_date(day, month, time):
                    movie_obj.date = movie_date
                else:
                    break
                movie_obj.location = (
                    "Lugar de la Memoria - Bajada San Martín 151 (Miraflores)"
                )
                movie_obj.center = "lum"
                movie_obj.source_url = page.url
                break

            if movie_obj.date:
                movies_to_return.append(movie_obj)
            else:
                continue

        return movies_to_return

    def _clean_title(self, event_title: str) -> str:
        if match := TITLE_PATTERN.search(event_title):
            return match.group(1).strip()

        return event_title.strip()
