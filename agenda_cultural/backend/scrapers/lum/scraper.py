import re
from datetime import datetime
from typing import override
from playwright.async_api import async_playwright, Page
from agenda_cultural.backend.models import Movies
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.services.tmdb_service import get_movie_poster
from agenda_cultural.backend.constants import MAPA_MESES

LUM = "https://lum.cultura.pe/actividades"
EVENT_BLOCK_SELECTOR = ".views-row"


class LumScraper(ScraperInterface):
    @override
    async def get_movies(self):
        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                _ = await page.goto(LUM, wait_until="load")

                events_block = await page.locator(EVENT_BLOCK_SELECTOR).count()

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
                            await self._get_movies_info(page)

            except Exception as e:
                print(e)
                return [Movies()]

            finally:
                await browser.close()

    async def _get_movies_info(self, page: Page):
        events = await page.locator(".field-item p strong").count()

        for event in range(events):
            if (
                "cine"
                in (
                    await page.locator(".field-item p strong").nth(event).inner_text()
                ).lower()
            ):
                event_title = await page.locator(".field-item p strong").nth(event).inner_text()
                clean_title = self._clean_title(event_title)

    async def _clean_title(self, event_title: str):
        pass
