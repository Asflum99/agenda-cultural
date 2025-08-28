import pytest
from typing import override
from playwright.async_api import async_playwright
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.models import Movie


class TestableScraperInterface(ScraperInterface):
    @override
    async def get_movies(self) -> list[Movie]:
        return []


class TestSetupBrowserAndOpenPage:
    @pytest.mark.integration
    async def test_setup_browser_and_open_page(self):
        scraper = TestableScraperInterface()
        async with async_playwright() as p:
            browser, page = await scraper.setup_browser_and_open_page(p)
            assert browser is not None
            assert page is not None
            assert hasattr(browser, "new_page")
            assert hasattr(page, "goto")
            await browser.close()
