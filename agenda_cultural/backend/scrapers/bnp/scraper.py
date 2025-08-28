import locale
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import override
from playwright.async_api import async_playwright, Page
from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface


class BnpScraper(ScraperInterface):
    BNP: str = "https://eventos.bnp.gob.pe/externo/inicio"
    MOVIE_BLOCK: str = ".no-padding.portfolio"
    MOVIE_TITLE_PATTERN: str = r"(.+?)(\s\(\d+\))"

    @override
    async def get_movies(self):
        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                movies = await self._count_movies(page)

                movies_info: list[Movie] = []

                for movie in range(movies):
                    if movie_info := await self._get_movies_info(movie, page):
                        movies_info.append(movie_info)

                return movies_info

            except Exception as e:
                print(e)
                return [Movie()]

            finally:
                await browser.close()

    async def _get_movies_info(self, movie: int, page: Page):
        try:
            movie_obj = Movie()

            async with page.context.expect_page() as new_page_info:
                await page.locator(self.MOVIE_BLOCK).nth(movie).click()

            new_page = await new_page_info.value
            await new_page.wait_for_load_state("load")

            if title := await new_page.locator(
                "#ContentPlaceHolder1_gpCabecera h1"
            ).text_content():
                if match := re.match(self.MOVIE_TITLE_PATTERN, title):
                    movie_obj.title = match.group(1)

            if date_time_element := await new_page.locator(
                "#ContentPlaceHolder1_gpDetalleEvento p:nth-child(2)"
            ).text_content():
                raw_date = date_time_element.strip()
                date = raw_date.replace("   ", " ")
                date = self._transform_date_to_iso(date)

                # Confirmar si la película ya se proyectó, ya que BNP muestra películas ya proyectadas
                if date < datetime.now(tz=ZoneInfo("America/Lima")):
                    return None

                movie_obj.date = date

            if location := await new_page.locator(
                "#ContentPlaceHolder1_gpUbicacion p"
            ).text_content():
                location = self._clean_location(location)
                movie_obj.location = location

            movie_obj.center = "bnp"

            await new_page.close()

            return movie_obj

        except Exception as e:
            print(e)

    def _clean_location(self, location: str):
        pos = location.find("Biblioteca")
        if pos != -1:
            result = location[pos:]
            result = result.replace(",", " -")
            return result
        else:
            return location

    def _transform_date_to_iso(self, date: str):
        _ = locale.setlocale(locale.LC_TIME, "es_PE.utf8")
        date = date[0].lower() + date[1:]
        date = self._minus_month(date)
        new_date = datetime.strptime(date, "%A, %d de %B del %Y %-I:%M%p")
        new_date = new_date.replace(tzinfo=ZoneInfo("America/Lima"))
        return new_date

    def _minus_month(self, date: str):
        months = {
            "Enero": "enero",
            "Febrero": "febrero",
            "Marzo": "marzo",
            "Abril": "abril",
            "Mayo": "mayo",
            "Junio": "junio",
            "Julio": "julio",
            "Agosto": "agosto",
            "Septiembre": "setiembre",
            "Octubre": "octubre",
            "Noviembre": "noviembre",
            "Diciembre": "diciembre",
        }
        for original_month, system_month in months.items():
            if original_month in date:
                return date.replace(original_month, system_month)

        raise ValueError(f"No se pudo parsear la fecha: {date}")

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
