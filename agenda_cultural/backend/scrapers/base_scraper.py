from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import ClassVar

from playwright.async_api import Browser, Page, Playwright

from agenda_cultural.backend.constants import MAPA_MESES
from agenda_cultural.backend.models import Movie


class ScraperInterface(ABC):
    """
    Clase base abstracta que define la interfaz común y herramientas compartidas
    para todos los scrapers de centros culturales.

    Esta clase no debe ser instanciada directamente. Se debe heredar de ella
    e implementar el método `get_movies`.
    """

    # Argumentos para optimizar Chromium en entornos Docker/Headless
    CHROMIUM_ARGS: ClassVar[list[str]] = [
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
    ]

    # User Agent genérico de Chrome en Windows para evitar bloqueos simples
    USER_AGENT: ClassVar[str] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    @abstractmethod
    async def get_movies(self) -> list[Movie]:
        """
        Método abstracto principal que debe implementar cada scraper hijo.

        Returns:
            list[Movie]: La lista de películas validadas y listas para guardar.
        """
        pass

    async def setup_browser_and_open_page(self, p: Playwright) -> tuple[Browser, Page]:
        """
        Configura e inicia una instancia de Chromium optimizada para scraping.

        Aplica flags específicos para mejorar el rendimiento

        Args:
            p (Playwright): Objeto gestor de Playwright.

        Returns:
            tuple[Browser, Page]: Una tupla conteniendo la instancia del navegador
            y la página (tab) creada.
        """
        browser = await p.chromium.launch(
            headless=True,
            args=self.CHROMIUM_ARGS,
        )

        context = await browser.new_context(user_agent=self.USER_AGENT)
        page = await context.new_page()
        return browser, page

    def validate_and_build_date(
        self,
        day: int,
        month_str: str,
        time_str: str,
        explicit_year: int | None = None,
    ) -> datetime | None:
        """
        Construye un objeto datetime a partir de fragmentos de fecha crudos.

        Realiza limpieza de texto, conversión de formatos de hora (AM/PM) e
        intenta inferir el año correcto si no se provee uno (lógica de cambio de año).

        Args:
            day (int): Día del mes (ej: 15).
            month_str (str): Nombre del mes en texto (ej: "Enero", "Set", "Octubre").
            time_str (str): Hora en texto crudo (ej: "7:00 pm", "19:00").
            explicit_year (int, optional): Año explícito si la web lo provee.
                                           Defaults to None.

        Returns:
            Optional[datetime]: Objeto datetime si la fecha es válida y futura (o de hoy).
                                Retorna None si hay error de parseo o es un evento pasado.
        """
        try:
            # 1. Validar y normalizar el mes
            month = MAPA_MESES.get(month_str.lower())
            if not month:
                return None

            # 2. Parsear y limpiar la hora
            clean_time = (
                time_str.replace(".", "")
                .replace("p m", "pm")
                .replace("a m", "am")
                .upper()
                .strip()
            )

            time_obj = None

            # Lista de formatos aceptados.
            possible_formats: list[str] = ["%I:%M %p", "%I:%M%p"]

            for fmt in possible_formats:
                try:
                    time_obj = datetime.strptime(clean_time, fmt).time()
                    break
                except ValueError:
                    continue

            if time_obj is None:
                # No se pudo entender el formato de hora
                return None

            # 3. Determinar Año
            now = datetime.now()

            if explicit_year:
                # Caso A: La web dice explícitamente el año
                year = explicit_year
                dt_obj = datetime(year, month, day, time_obj.hour, time_obj.minute)
            else:
                # Caso B: Inferencia dinámica
                year = now.year
                dt_obj = datetime(year, month, day, time_obj.hour, time_obj.minute)

                # Si la fecha construida es MUY antigua (ej: scrapeamos en Dic eventos de Ene),
                # asumimos que es del próximo año.
                # Umbral: 90 días hacia atrás.
                if dt_obj < (now - timedelta(days=90)):
                    dt_obj = dt_obj.replace(year=year + 1)

            # 4. Filtro de "Eventos Pasados"
            # Ignoramos películas que ocurrieron antes de la medianoche de hoy.
            midnight_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

            if dt_obj >= midnight_today:
                return dt_obj

            return None

        except (ValueError, IndexError, AttributeError):
            # Captura errores generales de conversión para no romper el scraper completo
            return None
