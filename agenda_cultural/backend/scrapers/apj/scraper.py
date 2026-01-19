import re
from datetime import datetime
from typing import ClassVar, Pattern, override

from playwright.async_api import Locator, Page, async_playwright

from agenda_cultural.backend.constants import MAPA_MESES
from agenda_cultural.backend.log_config import get_task_logger
from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.services.tmdb_service import get_movie_poster

logger = get_task_logger("lum_scraper", "scraping.log")


class ApjScraper(ScraperInterface):
    START_URL: ClassVar[str] = "https://www.apj.org.pe/cultural/agenda-cultural"
    CENTER_SLUG: ClassVar[str] = "apj"
    CENTER_LOCATION: ClassVar[str] = (
        "Centro Cultural Peruano Japonés - Av. Gregorio Escobedo 803, Residencial San Felipe (Jesús María)"
    )

    CATEGORIES_BLOCK_SELECTOR: ClassVar[str] = ".filter-agenda"

    WEEKS_SELECTOR: ClassVar[str] = ".rowTable:not(.rowTitle)"
    DAYS_SELECTOR: ClassVar[str] = ".cellTable"
    EVENT_SELECTOR: ClassVar[str] = ".cont-buttons"

    @override
    async def get_movies(self):
        movies: list[Movie] = []

        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                cinema_filter_found = False
                await page.goto(self.START_URL, wait_until="load")

                # Aplica el filtro de "Cine"
                categories_locator = page.locator(self.CATEGORIES_BLOCK_SELECTOR)
                total_categories = await categories_locator.count()

                for category in range(total_categories):
                    category_locator = categories_locator.nth(category)

                    category_name = await category_locator.inner_text()

                    if "cine" in category_name.lower():
                        await category_locator.click()
                        cinema_filter_found = True

                # Busca las películas a proyectarse
                if cinema_filter_found:
                    weeks_locator = page.locator(self.WEEKS_SELECTOR)
                    total_weeks = await weeks_locator.count()

                    for week in range(total_weeks):
                        current_week = weeks_locator.nth(week)
                        days_locator = current_week.locator(self.DAYS_SELECTOR)
                        total_days = await days_locator.count()

                        for day in range(total_days):
                            if current_day := days_locator.locator(self.EVENT_SELECTOR):
                                if await current_day.inner_text():
                                    pass

            except Exception as e:
                logger.error(f"Error en APJ Scraper: {e}", exc_info=True)

            finally:
                await browser.close()

        return movies
