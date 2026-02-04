"""
Módulo de Scraping para el Lugar de la Memoria (LUM).

Este módulo implementa la lógica de extracción de eventos cinematográficos
desde la agenda oficial del LUM.

TARGET URL: https://lum.cultura.pe/actividades

ESTRATEGIA DE NAVEGACIÓN:
1. Identificación de Bloques: Escanea la página principal buscando bloques de actividades.
2. Filtrado Inteligente:
   - Descarta agendas "Semanales".
   - Prioriza agendas "Mensuales" vigentes o futuras.
   - Entra a la página detalle de la agenda mensual seleccionada.

ESTRATEGIA DE EXTRACCIÓN (PARSING):
El HTML del LUM tiene las siguientes particularidades:
- Los eventos no están en contenedores <div> individuales.
- Se presentan como una secuencia de párrafos (<p>) con etiquetas <br>.
- Se utiliza la etiqueta <strong> como ancla principal para detectar títulos.

LÓGICA HEURÍTICA:
- Detección de Cine:
    Estrategia #1: Busca keywords ("Cine", "Documental") dentro de etiquetas <strong>.
    Estrategia #2: Buscar estructura (apertura de comillas) dentro de etiquetas <strong>.
- Desambiguación: Distingue entre encabezados (ej: "Cinefórum") y títulos reales
  analizando metadatos técnicos (Año, Duración) en las líneas adyacentes.
- Extracción Posicional: Deduce Fecha y Hora basándose en su posición relativa
  respecto al título detectado.
"""

import re
import time
from datetime import datetime
from typing import ClassVar, Pattern, override

from playwright.async_api import Locator, Page, async_playwright

from agenda_cultural.backend.constants import MAPA_MESES
from agenda_cultural.backend.log_config import get_task_logger
from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface
from agenda_cultural.backend.services.tmdb_service import get_movie_poster

logger = get_task_logger("lum_scraper", "scraping.log")


class LumScraper(ScraperInterface):
    START_URL: ClassVar[str] = "https://lum.cultura.pe/actividades"
    MOVIE_KEYWORDS: ClassVar[tuple[str, ...]] = (
        "cine",
        "película",
        "documental",
        "proyección",
    )
    CENTER_SLUG: ClassVar[str] = "lum"
    CENTER_LOCATION: ClassVar[str] = (
        "Lugar de la Memoria - Bajada San Martín 151 (Miraflores)"
    )

    # Los selectores de la página principal de actividades
    EVENT_TITLE: ClassVar[str] = ".views-field-title a"

    # Los selectores de los párrafos donde está el contenido de las películas
    PARAGRAPH_SELECTOR: ClassVar[str] = ".field-item p"

    # Captura de texto entre comillas, con soporte para tipográficas y rectas
    TITLE_PATTERN: Pattern[str] = re.compile(
        r"""
    [“"]        # Comilla de apertura (normal o tipográfica)
    ([^”"]+)    # Grupo 1: Contenido (todo excepto comillas)
    [”"]        # Comilla de cierre
    """,
        re.VERBOSE,
    )

    # Patrón que identifica paréntesis con metadatos al final del título (para su eliminación).
    METADATA_PATTERN: Pattern[str] = re.compile(r"\s*\(.*?\)$")

    # Patrón de validación: Detecta si el texto contiene datos técnicos (año/min).
    TECHNICAL_METADATA = re.compile(
        r"""
        \(              # Paréntesis de apertura literal
        .*?             # Contenido variable (greedy mínimo)
        \b              # Límite de palabra (evita falsos positivos como 'admin')
        (
            19\d{2}|    # Años 1900-1999
            20\d{2}|    # Años 2000-2099
            min         # Duración
        )
        \b              # Límite de palabra
        .*?             # Contenido variable
        \)              # Paréntesis de cierre
    """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Patrón de limpieza: Captura y elimina el nombre del director de la película.
    DIRECTOR_PATTERN: Pattern[str] = re.compile(r",\s*de\s+.*$", re.IGNORECASE)

    PREFIX_PATTERN: Pattern[str] = re.compile(
        r"""
        ^                   # Inicio de la línea
        (                   # Grupo 1: Palabras clave
            proyección|
            documental|
            cine|
            estreno|
            cinefórum|
            conversatorio|
            ciclo
        )
        ([\s\+\w]*)?        # Grupo 2 (Opcional): Texto extra (espacios, +, letras)
        [:\.]?              # Opcional: Termina en dos puntos o punto
        \s* # Espacios finales sobrantes
    """,
        re.IGNORECASE | re.VERBOSE,
    )

    DATE_PATTERN: Pattern[str] = re.compile(r"(\d{1,2})\s+de\s+([a-zA-Z]+)")

    TIME_PATTERN: Pattern[str] = re.compile(
        r"""
        [1-9]:[0-5][0-9]        # 1-9:MM (ej: 7:00)
        \s*                     # Espacios opcionales
        p\.?\s*m\.?             # 'pm' o 'p.m.' o 'p. m.'
    """,
        re.VERBOSE | re.IGNORECASE,
    )

    MONTHS_PATTERN: Pattern[str] = re.compile(
        r"\b(" + "|".join(MAPA_MESES.keys()) + r")\b", re.IGNORECASE
    )

    @override
    async def get_movies(self):
        movies: list[Movie] = []

        async with async_playwright() as p:
            browser, page = await self.setup_browser_and_open_page(p)

            try:
                # ESTO SERÁ TEMPORAL
                logger.info(f"Starting navigation to {self.START_URL}")
                start_time = time.time()

                await page.goto(
                    self.START_URL, wait_until="domcontentloaded", timeout=45000
                )

                duration = time.time() - start_time
                logger.info(f"Navigation completed in {duration:.2f}s")

                # Verificar redirecciones
                if page.url != self.START_URL:
                    logger.warning(f"Redirect detected: {self.START_URL} -> {page.url}")
                # ESTO SERÁ TEMPORAL

                activity_blocks = await page.locator(self.EVENT_TITLE).all()

                for index, block in enumerate(activity_blocks):
                    title_clean = await self._extract_activity_title(block)

                    if not title_clean:
                        continue

                    if "semanal" in title_clean:
                        continue

                    if self._is_relevant_monthly_agenda(title_clean):
                        # Promesa de que al hacer click, haya un cambio de página (cambio de URL)
                        async with page.expect_navigation(
                            wait_until="domcontentloaded", timeout=15000
                        ):
                            await page.locator(self.EVENT_TITLE).nth(index).click()

                        if movies_scraped := await self._extract_movies_from_agenda(
                            page
                        ):
                            movies.extend(movies_scraped)
                            break

            except Exception as e:
                if "timeout" in str(e).lower():
                    logger.error(
                        f"Timeout detected during navigation to {self.START_URL}"
                    )
                    try:
                        logger.error(f"Page state at timeout - URL: {page.url}")
                    except Exception:
                        logger.error("Could not determine page state at timeout")

                logger.error(f"Error en LUM Scraper: {e}", exc_info=True)

            finally:
                await browser.close()

        return movies

    async def _extract_activity_title(self, block: Locator) -> str | None:
        """
        Extrae y normaliza el título del bloque de actividad.

        Retorna None si encuentra un texto vacío.
        """
        title_text = await block.inner_text()

        # En caso retorne una cadena vacía, sigue siendo str, pero es False
        if not title_text:
            return None

        return title_text.strip().lower()

    def _is_relevant_monthly_agenda(self, title: str) -> bool:
        """
        Determina si una agenda es vigente (mes actual o futuro) basándose en su título.

        Analiza el texto buscando el nombre de un mes y un año (ej: "Agenda Diciembre 2025").

        Returns:
            bool: True si la fecha detectada es igual o posterior al mes actual.
                  False si es pasada o si no se pudo extraer una fecha válida.
        """
        for month_name, month_num in MAPA_MESES.items():
            if month_name in title.lower():
                if year_match := re.search(r"20\d{2}", title):
                    year = int(year_match.group())

                    now = datetime.now()

                    # Normaliza ambas fechas al día 1 para comparar solo AÑO y MES
                    # evitando problemas si hoy es día 30 y el mes objetivo tiene 28 días
                    current_date = datetime(now.year, now.month, 1)
                    target_date = datetime(year, month_num, 1)

                    return target_date >= current_date

        return False

    async def _extract_movies_from_agenda(self, page: Page) -> list[Movie]:
        """
        Extrae las películas de la agenda mensual que aún no se proyectan.
        Para ello revisa cada párrafo en búsqueda del título del metraje y los limpia de posible ruido.

        Retorna una lista con los objetos Movie.
        """
        paragraphs = await page.locator(self.PARAGRAPH_SELECTOR).all()
        movies_found: list[Movie] = []

        for paragraph in paragraphs:
            lines = await self._extract_clean_lines(paragraph)

            if not lines:
                continue

            title_index = self._resolve_title_index(lines)

            if title_index == -1:
                continue

            date_index = self._resolve_date_index(lines, title_index)

            if date_index == -1:
                logger.warning(
                    f"Título detectado, pero no se halló línea con fecha: '{lines[title_index]}'"
                )
                continue

            if date_index + 1 >= len(lines):
                logger.warning(
                    f"Fecha encontrada, pero falta la línea de hora: '{lines[date_index]}'"
                )
                continue

            try:
                if movie := self._build_movie_from_lines(
                    lines, title_index, date_index, page.url
                ):
                    movies_found.append(movie)
            except Exception as e:
                logger.error(f"Error procesando líneas de parrafo: {e}")

        return movies_found

    def _build_movie_from_lines(
        self, lines: list[str], title_index: int, date_index: int, source_url: str
    ) -> Movie | None:
        """
        Ensambla el objeto Movie a partir de las líneas de texto y los índices identificados.
        Realiza la limpieza de título, parseo de fecha y obtención de póster.
        """
        raw_title = lines[title_index]
        raw_date = lines[date_index]
        raw_time = self._find_time_after_index(lines, date_index)
        if not raw_time:
            logger.error(
                f"No se encontró hora válida después de la fecha en índice {date_index}"
            )
            return None

        day, month_str = self._parse_lum_date_string(raw_date)
        movie_date = self.validate_and_build_date(day, month_str, raw_time)

        if not movie_date:
            return None

        clean_title = self._clean_title(raw_title)
        movie_poster = get_movie_poster(clean_title)

        return Movie(
            title=clean_title,
            location=self.CENTER_LOCATION,
            date=movie_date,
            center=self.CENTER_SLUG,
            poster_url=movie_poster,
            source_url=source_url,
        )

    def _resolve_date_index(self, lines: list[str], start_index: int) -> int:
        """
        Busca el índice de la línea que contiene la fecha (basado en nombres de meses).
        Retorna -1 si no se encuentra.
        """
        if start_index >= len(lines):
            return -1

        for j in range(start_index, len(lines)):
            line_lower = lines[j].lower()
            if self.MONTHS_PATTERN.search(line_lower):
                if re.search(r"\d", line_lower):
                    return j

        return -1

    def _resolve_title_index(self, lines: list[str]) -> int:
        """
        Analiza un párrafo línea por línea para identificar cuál contiene el nombre
        de la película, usando una jerarquía de confianza
        """
        keyword_index = -1

        # Estrategia 1: Busqueda por palabras clave (Cine, Película, etc)
        # Primero buscamos si el párrafo tiene un encabezado temático.
        for idx, line in enumerate(lines):
            if any(k in line.lower() for k in self.MOVIE_KEYWORDS):
                keyword_index = idx
                break

        if keyword_index != -1:
            # Caso borde: La palabra clave está en la última línea (no hay nada más que buscar)
            if keyword_index + 1 >= len(lines):
                return keyword_index

            current_line = lines[keyword_index]
            next_line = lines[keyword_index + 1]

            # Pre-calculamos indicadores de calidad para decidir donde está el título.
            curr_has_meta = self._has_technical_metadata(current_line)
            next_has_meta = self._has_technical_metadata(next_line)

            # Verificamos si hay un título explícito despuésde 'Cine:' o 'Proyección'
            # (Usamos > 3 para ignorar etiquetas vacías o con ruido)
            content_after_colon = current_line.split(":")[-1].strip()
            curr_has_colon_title = ":" in current_line and len(content_after_colon) > 3

            next_starts_quote = next_line.strip().startswith(('"', "“", "”"))

            # Jerarquía de decisión

            # 1. Si la línea de la palabra clave ya incluye la ficha técnica.
            if curr_has_meta:
                return keyword_index

            # 2. Si hay un nombre sustancial después de los dos puntos.
            elif curr_has_colon_title:
                return keyword_index

            # 3. Si la siguiente línea es la ficha técnica, el título es la actual
            elif next_has_meta:
                return keyword_index

            # 4. Si la siguiente línea empieza con comillas, el título se movió abajo
            elif next_starts_quote:
                return keyword_index + 1

            # Por defecto, nos quedamos con la línea donde encontramos la palabra clave
            return keyword_index

        # Estrategia 2: Busqueda por estructura
        # Si no dice "Cine:", buscamos líneas con comillas que tengan metadatos cerca
        for idx, line in enumerate(lines):
            clean_line = line.strip()

            starts_quote = clean_line.startswith(('"', "“", "”"))

            if not starts_quote:
                continue

            # Confirmamos que es una película si ella misma o la siguiente tienen (Año) o (Min)
            has_meta_here = self._has_technical_metadata(clean_line)
            has_meta_next = False
            if idx + 1 < len(lines):
                has_meta_next = self._has_technical_metadata(lines[idx + 1])

            if has_meta_here or has_meta_next:
                return idx

        return -1  # No se encontró nada que parezca una película

    async def _extract_clean_lines(self, paragraph: Locator) -> list[str] | None:
        """
        Extrae las líneas de texto de un párrafo si contiene un elemento <strong>.

        Retorna None si el párrafo no tiene elemento <strong>.
        """
        if await paragraph.locator("strong").count() == 0:
            return None

        full_text = await paragraph.inner_text()

        lines = [line.strip() for line in full_text.split("\n") if line.strip()]

        return lines if lines else None

    def _clean_title(self, raw_title: str) -> str:
        """
        Limpia títulos complejos usando extracción por comillas o limpieza de patrones.
        """
        quote_match = self.TITLE_PATTERN.search(raw_title)

        # Si el título a analizar tiene una o más palabras entre comillas
        # lo más probable es que sea el nombre de la película
        # así que retornamos eso.
        if quote_match:
            return quote_match.group(1).strip()

        # De lo contrario, limpiamos el título
        clean = raw_title

        clean = self.METADATA_PATTERN.sub("", clean)

        clean = self.DIRECTOR_PATTERN.sub("", clean)

        clean = self.PREFIX_PATTERN.sub("", clean)

        clean = clean.strip(' "“”.,')

        return clean

    def _find_time_after_index(self, lines: list[str], start_index: int) -> str | None:
        """
        Busca dinámicamente la hora en las líneas siguientes al índice de fecha.

        Args:
            lines: Lista de líneas de texto del párrafo
            start_index: Índice de la fecha para buscar después

        Returns:
            str | None: Texto de hora encontrado o None si no se encuentra
        """
        # Buscar en las siguientes 3 líneas máximo
        search_limit = min(start_index + 3, len(lines))

        for i in range(start_index + 1, search_limit):
            line = lines[i].strip()
            if not line:  # Skip líneas vacías
                continue

            if self.TIME_PATTERN.search(line):
                return line

        return None

    def _parse_lum_date_string(self, date_text: str) -> tuple[int, str]:
        """
        Parsea fechas con formato "DD de Mes" (ej: '14 de Enero').

        Retorna (0, "") si no encuentra coincidencias.
        """
        if match := self.DATE_PATTERN.search(date_text):
            day = int(match.group(1))
            month: str = match.group(2).lower()
            return day, month
        return 0, ""

    def _has_technical_metadata(self, text: str) -> bool:
        """Detecta si el texto parece ser una ficha técnica (año o duración entre paréntesis)."""
        return bool(self.TECHNICAL_METADATA.search(text))
