from abc import ABC, abstractmethod
from agenda_cultural.backend.models import Movies
from playwright.async_api import Playwright


class ScraperInterface(ABC):
    @abstractmethod
    async def get_movies(self) -> list[Movies]:
        pass

    async def setup_browser_and_open_page(self, p: Playwright):
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
        return browser, page
