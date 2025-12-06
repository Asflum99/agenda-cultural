import re
from datetime import datetime
from typing import override
from playwright.async_api import async_playwright, Page
from agenda_cultural.backend.models import Movies
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.services.tmdb_service import get_movie_poster


class BnpScraper(ScraperInterface):
    BNP: str = "https://eventos.bnp.gob.pe/externo/inicio"
    MOVIE_BLOCK: str = ".no-padding.portfolio"

    @override
    async def get_movies(self):
        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                movies = await self._count_movies(page)

                movies_info: list[Movies] = []

                for movie in range(movies):
                    if movie_info := await self._get_movies_info(movie, page):
                        movies_info.append(movie_info)

                return movies_info

            except Exception as e:
                print(e)
                return [Movies()]

            finally:
                await browser.close()

    async def _get_movies_info(self, movie: int, page: Page):
        try:
            movie_obj = Movies()

            async with page.context.expect_page() as new_page_info:
                await page.locator(self.MOVIE_BLOCK).nth(movie).click()

            new_page = await new_page_info.value
            await new_page.wait_for_load_state("load")

            if title := await new_page.locator(
                "#ContentPlaceHolder1_gpCabecera h1"
            ).text_content():
                title = title.strip()

                parts = re.split(r"\s\(\d+\)", title, maxsplit=1)
                raw_title = parts[0]

                clean_title = raw_title.strip("\"',.-“”")
                poster_url = get_movie_poster(clean_title)
                movie_obj.title = clean_title
                movie_obj.poster_url = poster_url

            if date_time_element := await new_page.locator(
                "#ContentPlaceHolder1_gpDetalleEvento p:nth-child(2)"
            ).text_content():
                raw_date = date_time_element.strip().replace("   ", " ")
                date = self._parse_date_string(raw_date)

                if date is None:
                    return None

                movie_obj.date = date

            if location := await new_page.locator(
                "#ContentPlaceHolder1_gpUbicacion p"
            ).text_content():
                location = self._clean_location(location)
                movie_obj.location = location

            movie_obj.center = "bnp"
            movie_obj.source_url = new_page.url

            await new_page.close()

            return movie_obj

        except Exception as e:
            print(e)

    def _parse_date_string(self, date_str: str) -> datetime | None:
        clean_str = date_str.replace(",", "").strip()
        tokens = clean_str.split()

        if len(tokens) < 7:
            return None

        return self.validate_and_build_date(
            day=int(tokens[1]),
            month_str=tokens[3],
            time_str=f"{tokens[6]}",
            explicit_year=int(tokens[5]),
        )

    @staticmethod
    def _clean_location(location: str):
        pos = location.find("Biblioteca")
        if pos != -1:
            result = location[pos:]
            result = result.replace(",", " -", count=1).replace(
                ", San Borja", " (San Borja)"
            )
            return result
        else:
            return location

    async def _count_movies(self, page: Page):
        _ = await page.goto(self.BNP, wait_until="load")

        initial_count = await page.locator(self.MOVIE_BLOCK).count()

        _ = await page.select_option("select#ContentPlaceHolder1_cboCategoria", "1")

        await page.locator("a#ContentPlaceHolder1_btnBuscarEventos").click()

        _ = await page.wait_for_function(
            f"""
            () => {{
                const currentCount = document.querySelectorAll('{self.MOVIE_BLOCK}').length;
                return currentCount !== {initial_count};
            }}
            """
        )

        return await page.locator(self.MOVIE_BLOCK).count()
