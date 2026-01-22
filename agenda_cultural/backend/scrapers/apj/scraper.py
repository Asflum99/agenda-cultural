import re
from datetime import datetime
from typing import ClassVar, Pattern, override

from playwright.async_api import Page, async_playwright

from agenda_cultural.backend.constants import MAPA_MESES
from agenda_cultural.backend.log_config import get_task_logger
from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.services.tmdb_service import get_movie_poster

logger = get_task_logger("apj_scraper", "scraping.log")


class ApjScraper(ScraperInterface):
    START_URL: ClassVar[str] = "https://www.apj.org.pe/cultural/agenda-cultural"
    CENTER_SLUG: ClassVar[str] = "apj"
    CENTER_LOCATION: ClassVar[str] = (
        "Centro Cultural Peruano Japonés - Av. Gregorio Escobedo 803, Residencial San Felipe (Jesús María)"
    )

    CATEGORIES_SELECTOR: ClassVar[str] = ".filter-agenda"

    WEEKS_SELECTOR: ClassVar[str] = ".rowTable:not(.rowTitle)"
    DAYS_SELECTOR: ClassVar[str] = ".cellTable"
    EVENT_SELECTOR: ClassVar[str] = ".btn-circle"
    BUTTON_SELECTOR: ClassVar[str] = "button"
    EVENT_LINK_SELECTOR: ClassVar[str] = ".card-event"
    EVENT_DETAILS: ClassVar[str] = ".text-details"
    FREE_MOVIE_KEYWORDS: ClassVar[list[str]] = ["libre", "gratis"]
    EVENT_GENERAL_DETAILS: ClassVar[str] = ".detalleConvocatoria p"
    DAYS: ClassVar[list[str]] = [
        "lunes",
        "martes",
        "miércoles",
        "jueves",
        "viernes",
        "sábado",
        "domingo",
    ]

    @override
    async def get_movies(self):
        movies: list[Movie] = []

        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                await page.goto(self.START_URL, wait_until="load")

                # Aplica el filtro de "Cine"
                cinema_filter = await self._apply_cinema_filter(page)

                if cinema_filter:
                    # Busca las películas a proyectarse
                    movies_found = await self._search_movie_proyections(page)

                    # Iterar sobre las películas
                    if movies_found:
                        await self._extract_movies_info(page, movies_found)

            except Exception as e:
                logger.error(f"Error en APJ Scraper: {e}", exc_info=True)

            finally:
                await browser.close()

        return movies

    async def _apply_cinema_filter(self, page: Page) -> bool:
        categories_locator = await page.locator(self.CATEGORIES_SELECTOR).all()

        for category in categories_locator:
            category_name = await category.inner_text()

            if "cine" in category_name.lower():
                await category.click()
                return True

        return False

    async def _search_movie_proyections(self, page: Page) -> list[str | None]:
        weeks_locator = await page.locator(self.WEEKS_SELECTOR).all()
        movies_links = []

        for week in weeks_locator:
            days_locator = await week.locator(self.DAYS_SELECTOR).all()

            for day in days_locator:
                day_number = await day.inner_text()
                if day_number:
                    button = day.locator(self.EVENT_SELECTOR)
                    if await button.count() > 0:
                        await day.locator(self.BUTTON_SELECTOR).click()
                        card_event = page.locator(self.EVENT_LINK_SELECTOR)
                        card_event_link = await card_event.get_attribute("href")
                        if card_event_link:
                            # Busca si la película es de entrada gratis
                            event_details = await card_event.locator(
                                self.EVENT_DETAILS
                            ).all()
                            for detail in event_details:
                                text = await detail.inner_text()
                                if any(
                                    keyword in text.lower()
                                    for keyword in self.FREE_MOVIE_KEYWORDS
                                ):
                                    movies_links.append(card_event_link)
                    else:
                        continue
                else:
                    continue

        return movies_links

    async def _extract_movies_info(self, page: Page, movies_found: list):
        for movie in movies_found:
            await page.goto(movie, wait_until="load")
            event_details = await page.locator(self.EVENT_GENERAL_DETAILS).all()
            for detail in event_details:
                text = await detail.inner_text()
                if text.lower() in self.DAYS:
                    continue
