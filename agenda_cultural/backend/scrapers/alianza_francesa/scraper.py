import re
from typing import override
from playwright.async_api import async_playwright, Page
from playwright.async_api import Locator
from datetime import datetime

from agenda_cultural.backend.models import Movies
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface


class AlianzaFrancesaScraper(ScraperInterface):
    ALIANZA_FRANCESA: str = (
        "https://aflima.org.pe/eventos/?post_type=evento&categoria%5B%5D=cine"
    )

    @override
    async def get_movies(self) -> list[Movies]:
        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                _ = await page.goto(
                    self.ALIANZA_FRANCESA, wait_until="domcontentloaded"
                )

                # Grupo de secciones que proyectan películas gratuitas
                free_movies = page.locator(".ctbtn", has_text="Ingreso libre")
                cine_locators = await free_movies.count()

                movies_info: list[Movies] = []

                for locator in range(cine_locators):
                    await self._enter_movie_page(locator, page, free_movies)

                    movies = await page.locator(".cajas_cont_item").count()

                    for movie in range(movies):
                        if movie_info := await self._get_movies_info(movie, page):
                            movies_info.append(movie_info)

                    _ = await page.go_back(wait_until="domcontentloaded")

                return self._order_movies(movies_info)

            except Exception as e:
                print(e)
                return []

            finally:
                await browser.close()

    async def _get_movies_info(self, movie: int, page: Page):
        try:
            movie_obj = Movies()
            movie_box = page.locator(".cajas_cont_item").nth(movie)

            blocks = await movie_box.locator(
                ".cajas_cont_item_info .cajas__info_fecha2"
            ).count()

            keys = ["date", "location"]
            for block in range(blocks):
                if (
                    raw_info := await movie_box.locator(
                        ".cajas_cont_item_info .cajas__info_fecha2"
                    )
                    .nth(block)
                    .text_content()
                ):
                    info = raw_info.replace("\n", " ").strip()
                    if info == "":
                        continue

                    if keys[block] == "date":
                        date_obj = self._parse_date_string(info)

                        if date_obj is None:
                            continue

                        movie_obj.date = date_obj
                    else:
                        # Explicación del regex:
                        # \(([^,]+)   -> Grupo 1: Busca paréntesis y captura todo hasta la coma (Avenida)
                        # ,\s* -> Busca una coma y espacios opcionales (los ignora)
                        # ([^)]+)     -> Grupo 2: Captura todo lo que no sea paréntesis de cierre (Distrito)
                        if match := re.search(r"\(([^,]+),\s*([^)]+)\)", info):
                            avenue = match.group(1).strip()
                            district = match.group(2).strip()
                            movie_obj.location = (
                                f"Alianza Francesa de {district} - {avenue}"
                            )

            if raw_title := await movie_box.locator(
                ".cajas_cont_item_fecha .cajas__fecha_txt"
            ).text_content():
                movie_obj.title = raw_title.replace("\n", " ").strip()

            movie_obj.center = "alianza francesa"

            return movie_obj
        except Exception as e:
            print(e)

    @staticmethod
    async def _enter_movie_page(locator: int, page: Page, free_movies: Locator):
        await free_movies.locator("a.btn-outline-primary").nth(locator).click()
        await page.wait_for_load_state("domcontentloaded")

    def _parse_date_string(self, date_str: str) -> datetime | None:
        try:
            clean_str = date_str.strip().rstrip(".")
            parts = clean_str.split(",")

            if len(parts) != 2:
                return None

            fecha_part = parts[0].strip()
            hora_part = parts[1].strip()

            fecha_tokens = fecha_part.split()

            if len(fecha_tokens) < 4:
                return None

            return self.validate_and_build_date(
                day=int(fecha_tokens[1]), month_str=fecha_tokens[3], time_str=hora_part
            )

        except (IndexError, ValueError):
            return None

    @staticmethod
    def _order_movies(movies: list[Movies]) -> list[Movies]:
        """Ordena las películas por fecha de proyección"""
        valid_movies = [m for m in movies if m.date is not None]
        return sorted(valid_movies, key=lambda m: m.date)  # pyright: ignore
