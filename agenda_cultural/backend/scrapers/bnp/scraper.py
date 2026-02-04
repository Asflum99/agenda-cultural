"""
Módulo de Scraping para la Biblioteca Nacional del Perú (BNP).

Este módulo implementa la lógica de extracción de eventos cinematográficos
desde la agenda oficial de Bibliocine de la BNP.

TARGET URL: https://eventos.bnp.gob.pe/externo/inicio

ESTRATEGIA DE NAVEGACIÓN:
1. Acceso a la página principal de eventos de la BNP.
2. Filtrado: Selecciona la categoría "Bibliocine" mediante un dropdown.
3. Espera dinámica: El sitio carga los eventos vía JavaScript tras aplicar el filtro.
4. Navegación por película: Abre cada película en una nueva pestaña para extraer
   detalles completos (título, fecha, ubicación). Esta estrategia evita perder el
   estado del filtro aplicado, ya que al volver a la página principal se resetearía
   el dropdown y habría que reaplicar el filtro en cada iteración.

ESTRATEGIA DE EXTRACCIÓN (PARSING):
El HTML de la BNP presenta los eventos de forma estructurada:
- Lista de bloques de películas en la página principal.
- Cada película tiene su propia página de detalle con:
    * Título en formato "Nombre de Película (Año)".
    * Fecha y hora en texto libre (ej: "15 de Enero del 2025 a las 7:00pm").
    * Ubicación detallada de la sala de proyección.

LÓGICA DE PROCESAMIENTO:
- Limpieza de título: Extrae el nombre y el año opcional usando regex.
- Parseo de fecha: Convierte el texto en español a componentes estructurados
  (día, mes, año, hora) para construir un datetime válido.
- Normalización de ubicación: Simplifica la dirección manteniendo solo
  la información relevante de la biblioteca/sala.
"""

import re
from datetime import datetime
from typing import ClassVar, Pattern, override

from playwright.async_api import Page, async_playwright

from agenda_cultural.backend.log_config import get_task_logger
from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.services.tmdb_service import get_movie_poster

logger = get_task_logger("bnp_scraper", "scraping.log")


class BnpScraper(ScraperInterface):
    """
    Scraper especializado para extraer información de proyecciones de
    Bibliocine desde la web de la Biblioteca Nacional del Perú.
    """

    START_URL: ClassVar[str] = "https://eventos.bnp.gob.pe/externo/inicio"
    MOVIE_BLOCK: ClassVar[str] = ".no-padding.portfolio"
    CENTER_SLUG: ClassVar[str] = "bnp"
    BIBLIOCINE_FILTER: ClassVar[str] = "select#ContentPlaceHolder1_cboCategoria"
    APPLY_FILTER_BUTTON: ClassVar[str] = "a#ContentPlaceHolder1_btnBuscarEventos"
    MOVIE_TITLE: ClassVar[str] = "#ContentPlaceHolder1_gpCabecera h1"
    MOVIE_INFO: Pattern[str] = re.compile(r"^(.+?)\s*(?:\(\s*(\d{4})\s*\))?\s*$")
    DATE_SELECTOR: ClassVar[str] = "#ContentPlaceHolder1_gpDetalleEvento p:nth-child(2)"
    DATE_PATTERN: Pattern[str] = re.compile(
        r"""
        (3[01]|[12]?[0-9])                                                                                      # Fecha de proyección (1-31, permite 01-09)
        \s*\w+\s*                                                                                               # Espacio y preposición
        (Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Setiembre|Septiembre|Octubre|Noviembre|Diciembre)    # Mes de proyección
        (?:\s*\w+)?\s*                                                                                          # "del" opcional entre mes y año
        (20\d{2})                                                                                               # Año de proyección (Contar del 20XX para adelante)
        \s*
        ((?:0?[1-9]|1[0-2]):[0-5][0-9]\s*[AP]M)                                                                 # Hora de proyección (01-12 con AM/PM, espacio opcional)
            """,
        re.VERBOSE | re.IGNORECASE,
    )
    LOCATION_SELECTOR: ClassVar[str] = "#ContentPlaceHolder1_gpUbicacion p"
    LOCATION_KEYWORDS: ClassVar[Pattern[str]] = re.compile(
        r"biblioteca|bnp", re.IGNORECASE
    )

    @override
    async def get_movies(self) -> list[Movie]:
        """
        Orquesta el proceso completo de scraping de Bibliocine.

        Flujo:
        1. Inicializa el navegador y carga la página principal.
        2. Aplica el filtro de categoría "Bibliocine".
        3. Itera sobre cada bloque de película encontrado.
        4. Extrae la información detallada de cada película.

        Returns:
            list[Movie]: Lista de películas extraídas y validadas.
                         Retorna lista vacía si ocurre un error crítico.
        """
        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            movies_extracted: list[Movie] = []

            try:
                logger.info("Iniciando scraping en BNP.")
                await page.goto(self.START_URL, wait_until="domcontentloaded")

                page = await self._apply_bibliocine_filter(page)

                if page is None:
                    raise RuntimeError(
                        "No se pudo aplicar el filtro de Bibliocine. La página retornó None"
                    )

                movies = await page.locator(self.MOVIE_BLOCK).count()

                for movie in range(movies):
                    if movie_info := await self._extract_movie_info(movie, page):
                        movies_extracted.append(movie_info)

                logger.info("Scraping terminado en BNP. Retornando películas.")

            except Exception as e:
                logger.error(f"Error en BNP Scraper: {e}", exc_info=True)

            finally:
                await browser.close()

            return movies_extracted

    async def _extract_movie_info(self, movie: int, page: Page) -> Movie | None:
        """
        Extrae la información completa de una película individual.

        Navega a la página de detalle de la película especificada y extrae:
        - Título limpio y año (opcional).
        - Fecha y hora de proyección.
        - Ubicación de la sala.
        - URL del póster (vía API externa).

        Args:
            movie: Índice de la película en la lista de resultados.
            page: Página principal del listado de eventos.

        Returns:
            Movie | None: Objeto Movie con los datos completos si la extracción
                         fue exitosa. None si falta información crítica o la
                         fecha es inválida.
        """

        movie_page = await self._open_movie_page(movie, page)
        if not movie_page:
            return None

        try:
            title_data = await self._extract_title(movie_page)
            if not title_data:
                return None
            movie_title, poster_url = title_data

            movie_date = await self._extract_date(movie_page, movie_title)
            if not movie_date:
                return None

            location = await self._extract_location(movie_page, movie_title)
            if not location:
                return None

            return Movie(
                title=movie_title,
                location=location,
                date=movie_date,
                center=self.CENTER_SLUG,
                poster_url=poster_url,
                source_url=movie_page.url,
            )
        finally:
            await movie_page.close()

    async def _extract_location(self, movie_page: Page, movie_title: str) -> str | None:
        """
        Extrae y limpia la ubicación de la sala de proyección.

        Obtiene el texto de la ubicación desde el selector correspondiente
        y lo limpia usando el método _clean_location.

        Args:
            movie_page: Página de detalle de la película.
            movie_title: Título de la película (para logging de errores).

        Returns:
            str | None: Nombre limpio de la ubicación/sala si se encuentra.
                       None si no se pudo extraer la ubicación.
        """
        if location := await movie_page.locator(self.LOCATION_SELECTOR).text_content():
            return self._clean_location(location)
        else:
            logger.warning(
                f"No se pudo encontrar la locación para la película {movie_title}."
            )
            return None

    async def _extract_date(
        self, movie_page: Page, movie_title: str
    ) -> datetime | None:
        """
        Extrae y parsea la fecha y hora de proyección de la película.

        Obtiene el texto de la fecha desde el selector correspondiente,
        lo limpia, lo parsea en componentes y construye un objeto datetime
        válido usando validate_and_build_date.

        Args:
            movie_page: Página de detalle de la película.
            movie_title: Título de la película (para logging de errores).

        Returns:
            datetime | None: Objeto datetime con la fecha y hora de proyección
                            si el parsing fue exitoso. None si no se pudo
                            extraer o parsear la fecha.
        """
        if raw_date := await movie_page.locator(self.DATE_SELECTOR).text_content():
            raw_date = raw_date.strip().replace("   ", " ")

            # Verifica si el parsing fue exitoso
            parsed_date = self._parse_date(raw_date)
            if parsed_date is None:
                logger.warning(
                    f"No se pudo parsear la fecha para la película {movie_title}."
                )
                return None

            day, month_str, year, time_str = parsed_date
            movie_date = self.validate_and_build_date(day, month_str, time_str, year)

            if movie_date is None:
                logger.warning(
                    f"No se pudo establecer la fecha completa para la película {movie_title}."
                )
                return None
            return movie_date
        else:
            logger.warning(
                f"No se pudo encontrar la fecha para la película {movie_title}."
            )
            return None

    async def _extract_title(self, movie_page: Page) -> tuple[str, str | None] | None:
        """
        Extrae el título, año y URL del póster de la película.

        Obtiene el texto del título desde el selector correspondiente,
        lo parsea para extraer el título limpio y el año opcional,
        y consulta la API externa para obtener la URL del póster.

        Args:
            movie_page: Página de detalle de la película.

        Returns:
            tuple[str, str | None] | None: Tupla con (título_limpio, url_póster)
                                           si la extracción fue exitosa. El url_póster
                                           es opcional.
                                           Retorna None si no se pudo extraer el título.
        """
        if raw_title := await movie_page.locator(self.MOVIE_TITLE).text_content():
            title_result = self._parse_title_and_year(raw_title)
            if title_result is None:
                logger.warning(f"No se pudo extraer el título del texto: {raw_title}")
                return None
            clean_title, movie_year = title_result
            poster_url = get_movie_poster(clean_title)
            return clean_title, poster_url
        else:
            logger.warning("No se encontró el título.")
            return None

    async def _open_movie_page(self, movie: int, page: Page) -> Page | None:
        """
        Abre la página de detalle de una película en una nueva pestaña.

        Hace clic en el bloque de película especificado y espera a que
        se abra una nueva pestaña con la página de detalles.

        Args:
            movie: Índice de la película en la lista de resultados.
            page: Página principal del listado de eventos.

        Returns:
            Page | None: Objeto Page de la nueva pestaña abierta si la
                        navegación fue exitosa. None si ocurrió un error.
        """
        try:
            # Promesa de que al hacer clic en la página se abrirá una nueva pestaña.
            # Luego espera a que el DOM cargue por completo para luego interactuar.
            async with page.context.expect_page() as new_page:
                await page.locator(self.MOVIE_BLOCK).nth(movie).click()
            movie_page = await new_page.value
            await movie_page.wait_for_load_state("domcontentloaded")
            return movie_page
        except Exception as e:
            logger.warning(f"Error al abrir la página de la película {movie}: {e}")
            return None

    def _parse_title_and_year(self, raw_title: str) -> tuple[str, str | None] | None:
        """
        Extrae el título limpio y el año opcional del título crudo.

        Utiliza un patrón regex para separar el nombre de la película de
        su año de estreno cuando viene en formato "Nombre (AAAA)".

        Args:
            raw_title: Título completo como aparece en la web.

        Returns:
            tuple[str, str | None] | None: Tupla con (título_limpio, año_opcional)
                                          si se encuentra el patrón. El año es None
                                          si no se especifica en el título.
                                          Retorna None si no hay match.
        """
        if movie_info := self.MOVIE_INFO.search(raw_title):
            clean_title = movie_info.group(1).strip()

            # Evita que pasen títulos vacíos
            if not clean_title:
                return None

            clean_year = movie_info.group(2) if movie_info.group(2) else None
            return clean_title, clean_year
        return None

    def _parse_date(self, date_str: str) -> tuple[int, str, int, str] | None:
        """
        Parsea el texto de fecha en componentes estructurados.

        Busca patrones como "15 de Enero del 2025 a las 7:00PM" y extrae
        día, mes (como string), año y hora.

        Args:
            date_str: Texto de fecha crudo de la página.

        Returns:
            tuple[int, str, int, str] | None: Tupla con (día, mes, año, hora)
                                             si se encuentra el patrón.
                                             None si no hay coincidencia.
        """
        if match := self.DATE_PATTERN.search(date_str):
            day = int(match.group(1))
            if day == 0:
                return None  # Día 0 no es válido
            month_str = match.group(2)
            year = int(match.group(3))
            time_str = match.group(4)

            # Normaliza la hora: quita espacios y cero inicial de la hora
            time_str = time_str.replace(" ", "").lstrip("0") or "0"

            return day, month_str, year, time_str
        else:
            return None

    async def _apply_bibliocine_filter(self, page: Page) -> Page | None:
        """
        Aplica el filtro de categoría "Bibliocine" en la página de eventos.

        Selecciona la categoría en el dropdown y espera a que el DOM
        se actualice dinámicamente con los eventos de cine.

        Args:
            page: Página principal de eventos.

        Returns:
            Page | None: La misma página actualizada con los resultados filtrados.
                        None si ocurre un error durante el proceso.
        """
        initial_count = await page.locator(self.MOVIE_BLOCK).count()

        await page.select_option(self.BIBLIOCINE_FILTER, "1")

        await page.locator(self.APPLY_FILTER_BUTTON).click()

        await page.wait_for_function(
            f"""
            () => {{
                const currentCount = document.querySelectorAll('{self.MOVIE_BLOCK}').length;
                return currentCount !== {initial_count};
            }}
            """
        )

        return page

    def _clean_location(self, location: str) -> str:
        """
        Normaliza el texto de ubicación buscando keywords clave.

        Busca "biblioteca" o "bnp" (case-insensitive) y extrae desde
        la primera ocurrencia encontrada.

        Args:
            location: Texto de ubicación crudo de la página.

        Returns:
            str: Ubicación limpia y formateada. Si no encuentra keywords,
                 retorna el texto original.
        """
        if match := self.LOCATION_KEYWORDS.search(location):
            pos = match.start()
            result = location[pos:]
            result = result.replace(",", " -", count=1).replace(
                ", San Borja", " (San Borja)"
            )
            return result
        else:
            return location
