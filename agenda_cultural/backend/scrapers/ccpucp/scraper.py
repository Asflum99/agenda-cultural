import re
from datetime import datetime
from typing import override
from playwright.async_api import async_playwright, Page
from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.services.tmdb_service import get_movie_poster

CCPUCP = "https://centrocultural.pucp.edu.pe/cine.html"
MOVIE_TITLE_SELECTOR = ".catItemTitle a"


class CcpucpScraper(ScraperInterface):
    @override
    async def get_movies(self):
        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                _ = await page.goto(CCPUCP, wait_until="load")

                movies_block = await page.locator("a.subCategoryImage").count()

                movies_info: list[Movie] = []

                for movie_block in range(movies_block):
                    await page.locator("a.subCategoryImage").nth(movie_block).click()
                    await page.wait_for_load_state("load")
                    movies = await page.locator(MOVIE_TITLE_SELECTOR).count()

                    for movie in range(movies):
                        if movie_info := await self._get_movies_info(movie, page):
                            movies_info.append(movie_info)
                        _ = await page.go_back(wait_until="load")

                    _ = await page.go_back(wait_until="load")

                return movies_info

            except Exception as e:
                print(e)
                return [Movie()]

            finally:
                await browser.close()

    async def _get_movies_info(self, movie: int, page: Page):
        try:
            movie_obj = Movie()

            movie_title = (
                await page.locator(MOVIE_TITLE_SELECTOR).nth(movie).inner_text()
            )
            await page.locator(MOVIE_TITLE_SELECTOR).nth(movie).click()
            await page.wait_for_load_state("load")

            # Verificar si la película es con entradas
            if await page.locator('p:has(span b:has-text("ENTRADAS"))').count() > 0:
                return None

            fecha_locator = page.locator(
                'p:has(span strong:text("FUNCIONES")) span'
            ).filter(
                has_text=re.compile(
                    r"(lunes|martes|miércoles|jueves|viernes|sábado|domingo)\s+\d{1,2}\s+de\s+\w+"
                )
            )
            if date_exist := await fecha_locator.text_content():
                date_object = self._parse_date_string(date_exist)

                if date_object:
                    clean_title = self._clean_title(movie_title)
                    poster_url = get_movie_poster(clean_title)
                    movie_obj.date = date_object
                    movie_obj.title = clean_title
                    movie_obj.location = "CCPUCP - Av. Camino Real 1075 (San Isidro)"
                    movie_obj.center = "ccpucp"
                    movie_obj.poster_url = poster_url
                    movie_obj.source_url = page.url

                    return movie_obj
                else:
                    return None
            else:
                return None

        except Exception as e:
            print(e)

    def _parse_date_string(self, date_str: str) -> datetime | None:
        parts = date_str.split("|")
        if len(parts) != 2:
            return None

        fecha_tokens = parts[0].split()
        hora_str = parts[1]

        return self.validate_and_build_date(
            day=int(fecha_tokens[1]), month_str=fecha_tokens[3], time_str=hora_str
        )

    @staticmethod
    def _clean_title(movie_title: str):
        movie = movie_title.lower()
        movie_words = movie.split()
        movie_words[0] = movie_words[0].capitalize()
        return " ".join(movie_words)
