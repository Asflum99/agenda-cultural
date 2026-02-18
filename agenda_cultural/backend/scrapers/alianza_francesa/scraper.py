import re
from datetime import datetime
from typing import ClassVar, Pattern, override

from playwright.async_api import Locator, Page, async_playwright

from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.services.tmdb_service import get_movie_poster


class AlianzaFrancesaScraper(ScraperInterface):
    START_URL: ClassVar[str] = (
        "https://aflima.org.pe/eventos/?post_type=evento&categoria[]=cine"
    )
    DATE_PATTERN: Pattern[str] = re.compile(
        r"(?i)(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre),\s+(\d{1,2}:\d{2})\s+([ap]\.?\s?m\.?)"
    )

    @override
    async def get_movies(self) -> list[Movie]:
        movies: list[Movie] = []

        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                await page.goto(self.START_URL, wait_until="domcontentloaded")

                # Grupo de secciones que proyectan películas gratuitas
                free_movies_locator = await page.locator(
                    ".ctbtn", has_text="Ingreso libre"
                ).all()

                for free_movie in free_movies_locator:
                    await free_movie.locator("a.btn-outline-primary").click()
                    await page.wait_for_load_state("domcontentloaded")

                    free_movies = await page.locator(".cajas_cont_item.cine").all()

                    for free_movie in free_movies:
                        if movie_info := await self._get_movie_info(free_movie, page):
                            movies.append(movie_info)

                    await page.go_back(wait_until="domcontentloaded")

                return self._order_movies(movies)

            except Exception as e:
                print(e)
                return []

            finally:
                await browser.close()

    async def _get_movie_info(self, movie: Locator, page: Page):
        try:
            movie_info = movie.locator(".cajas_cont_item_info")

            raw_movie_date_and_location = await movie_info.locator(
                ".cajas__info_fecha2"
            ).all()

            keys = ["date", "location"]
            for block in raw_movie_date_and_location:
                raw_info = await block.text_content()
                if not raw_info:
                    continue

                if raw_date := self.DATE_PATTERN.search(raw_info):
                    pass
                if (
                    raw_info := await movie.locator(
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

                        movie_date = date_obj
                    else:
                        # Explicación del regex:
                        # \(([^,]+)   -> Grupo 1: Busca paréntesis y captura todo hasta la coma (Avenida)
                        # ,\s* -> Busca una coma y espacios opcionales (los ignora)
                        # ([^)]+)     -> Grupo 2: Captura todo lo que no sea paréntesis de cierre (Distrito)
                        if match := re.search(r"\(([^,]+),\s*([^)]+)\)", info):
                            avenue = match.group(1).strip()
                            district = match.group(2).strip()
                            location = f"Alianza Francesa de {district} - {avenue}"

            if raw_title := await movie.locator(
                ".cajas_cont_item_fecha .cajas__fecha_txt"
            ).text_content():
                clean_title = raw_title.replace("\n", " ").strip()
                poster_url = get_movie_poster(clean_title)
                movie_title = clean_title
                poster_url = poster_url

            return Movie(
                title=movie_title,
                location=location,
                date=movie_date,
                center="af",
                poster_url=poster_url,
                source_url=page.url,
            )
        except Exception as e:
            print(e)

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
    def _order_movies(movies: list[Movie]) -> list[Movie]:
        """Ordena las películas por fecha de proyección"""
        valid_movies = [m for m in movies if m.date is not None]
        return sorted(valid_movies, key=lambda m: m.date)
