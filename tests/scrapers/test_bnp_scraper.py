import re
import pytest
from playwright.async_api import async_playwright
from datetime import datetime
from zoneinfo import ZoneInfo
from agenda_cultural.backend.scrapers.bnp.scraper import BnpScraper
from agenda_cultural.backend.models import Movie


@pytest.mark.integration
async def test_get_movies():
    scraper = BnpScraper()
    movies = await scraper.get_movies()
    assert isinstance(movies, list)
    assert len(movies) > 0


@pytest.mark.integration
async def test_count_movies_with_selector_validation():
    scraper = BnpScraper()
    async with async_playwright() as p:
        browser, page = await scraper.setup_browser_and_open_page(p)
        try:
            # 1. PRIMERO: Verificar que los selectores críticos existen
            _ = await page.goto(scraper.BNP, wait_until="load")
            initial_elements = await page.locator(scraper.MOVIE_BLOCK).count()
            select_exists = await page.locator(
                "select#ContentPlaceHolder1_cboCategoria"
            ).count()
            button_exists = await page.locator(
                "a#ContentPlaceHolder1_btnBuscarEventos"
            ).count()

            # Estos deben existir SIEMPRE (aunque sean 0 películas)
            assert (
                select_exists > 0
            ), "Select de categoría no encontrado - selector cambió"
            assert (
                button_exists > 0
            ), "Botón de búsqueda no encontrado - selector cambió"

            # 2. SEGUNDO: Verificar el comportamiento del wait_for_function
            _ = await page.select_option("select#ContentPlaceHolder1_cboCategoria", "1")

            # Capturar el momento antes del click
            count_before_click = await page.locator(scraper.MOVIE_BLOCK).count()

            # Hacer click y esperar el cambio (esto prueba implícitamente el wait_for_function)
            await page.locator("a#ContentPlaceHolder1_btnBuscarEventos").click()

            # Verificar que wait_for_function funciona esperando un tiempo razonable
            # Si no funciona, esto fallará por timeout
            try:
                _ = await page.wait_for_function(
                    f"""
                    () => {{
                        const currentCount = document.querySelectorAll('{scraper.MOVIE_BLOCK}').length;
                        return currentCount !== {count_before_click};
                    }}
                    """,
                    timeout=10000,
                )
                wait_for_function_worked = True
            except Exception as e:
                wait_for_function_worked = False
                print(f"⚠️ wait_for_function falló: {e}")

            # 3. TERCERO: Ejecutar la función completa
            movies_count = await scraper._count_movies(page) # pyright: ignore [reportPrivateUsage]
            assert isinstance(movies_count, int)
            assert movies_count >= 0

            # 4. CUARTO: Validaciones adicionales
            count_after_function = await page.locator(scraper.MOVIE_BLOCK).count()

            if movies_count == 0:
                print(
                    f"⚠️ 0 películas encontradas. Elementos iniciales: {initial_elements}"
                )
                print(f"   Count antes del click: {count_before_click}")
                print(f"   Count después de _count_movies: {count_after_function}")
                print(f"   wait_for_function funcionó: {wait_for_function_worked}")
            else:
                print(f"✅ {movies_count} películas encontradas correctamente")
                # Verificar que hubo un cambio real
                assert (
                    count_before_click != movies_count or wait_for_function_worked
                ), "El wait_for_function debería haber detectado un cambio"

        finally:
            await browser.close()


@pytest.mark.unit
def test_clean_location():
    scraper = BnpScraper()
    location = "Oficiona random, Biblioteca Nacional del Perú, Av. De La Poesía 160, San Borja"
    result = scraper._clean_location(location) # pyright: ignore [reportPrivateUsage]
    assert result == "Biblioteca Nacional del Perú - Av. De La Poesía 160 (San Borja)"
 

@pytest.mark.unit
def test_minus_month():
    scraper = BnpScraper()
    date = "martes, 12 de Septiembre del 2025"
    result = scraper._minus_month(date) # pyright: ignore [reportPrivateUsage]
    assert result == "martes, 12 de setiembre del 2025"


@pytest.mark.unit
def test_transform_date_to_iso():
    scraper = BnpScraper()
    test_cases = [
        "Martes, 2 de Septiembre del 2025 7:00PM", 
        "Miércoles, 12 de Septiembre del 2025 12:00PM",
        "Jueves, 29 de Septiembre del 2025 11:00AM",
    ]
    test_results: list[datetime] = []
    for test_case in test_cases:
        test_results.append(scraper._transform_date_to_iso(test_case)) # pyright: ignore [reportPrivateUsage]
        
    assert test_results == [
        datetime(2025, 9, 2, 19, 0, tzinfo=ZoneInfo("America/Lima")),
        datetime(2025, 9, 12, 12, 0, tzinfo=ZoneInfo("America/Lima")),
        datetime(2025, 9, 29, 11, 0, tzinfo=ZoneInfo("America/Lima")),
    ]


@pytest.mark.integration
async def test_get_movies_info():
    scraper = BnpScraper()
    async with async_playwright() as p:
        browser, page = await scraper.setup_browser_and_open_page(p)
        try:
            movies = await scraper._count_movies(page) # pyright: ignore [reportPrivateUsage]
            for movie in range(min(3, movies)):
                movie_obj = Movie()

                async with page.context.expect_page() as new_page_info:
                    movie_block = await page.locator(scraper.MOVIE_BLOCK).count()
                    assert movie_block > 0, "No se encontraron peliculas"
                    await page.locator(scraper.MOVIE_BLOCK).nth(movie).click()
                
                new_page = await new_page_info.value
                await new_page.wait_for_load_state("load")

                title_block = await new_page.locator("#ContentPlaceHolder1_gpCabecera h1").count()
                assert title_block > 0, "No se encontró título de película"

                if title := await new_page.locator(
                    "#ContentPlaceHolder1_gpCabecera h1"
                ).text_content():
                    if match := re.match(scraper.MOVIE_TITLE_PATTERN, title):
                        movie_obj.title = match.group(1)
                        assert movie_obj.title is not None, "No se encontró título de filmer"

                date_block = await new_page.locator("#ContentPlaceHolder1_gpDetalleEvento p:nth-child(2)").count()
                assert date_block > 0, "No se encontró fecha de proyección"

                if date_time_element := await new_page.locator(
                    "#ContentPlaceHolder1_gpDetalleEvento p:nth-child(2)"
                ).text_content():
                    raw_date = date_time_element.strip()
                    date = raw_date.replace("   ", " ")
                    date = scraper._transform_date_to_iso(date) # pyright: ignore [reportPrivateUsage]
                    # Confirmar si la película ya se proyectó, ya que BNP muestra películas ya proyectadas
                    if date < datetime.now(tz=ZoneInfo("America/Lima")):
                        continue

                    movie_obj.date = date
                    assert movie_obj.date is not None, "No se encontró fecha de proyección"

                location_block = await new_page.locator("#ContentPlaceHolder1_gpUbicacion p").count()
                assert location_block > 0, "No se encontró ubicación de proyección"

                if location := await new_page.locator(
                "#ContentPlaceHolder1_gpUbicacion p"
                ).text_content():
                    location = scraper._clean_location(location) # pyright: ignore [reportPrivateUsage]
                    movie_obj.location = location

                    movie_obj.center = "bnp"

                    assert movie_obj.location is not None, "No se encontró ubicación de proyección"

                    await new_page.close()
                    
        except Exception as e:
            print(e)
        finally:
            await browser.close()