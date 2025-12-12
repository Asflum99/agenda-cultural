from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from playwright.async_api import Playwright
from agenda_cultural.backend.constants import MAPA_MESES
from agenda_cultural.backend.models import Movies


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

    def validate_and_build_date(
        self, day: int, month_str: str, time_str: str, explicit_year: int | None = None
    ) -> datetime | None:
        """
        Método universal para construir fechas.
        Recibe las piezas crudas, las valida y aplica la lógica de negocio (medianoche, año nuevo).
        """
        try:
            # 1. Validar Mes
            month = MAPA_MESES.get(month_str.lower())
            if not month:
                return None

            # 2. Parsear Hora (Maneja "7:00 pm", "7:00 p.m.", "19:00", "7:00 p. m.")
            clean_time = time_str.replace(".", "").replace("p m", "pm").upper().strip()

            # Asumimos formato AM/PM. Si algún cine usa 24h, habría que ajustar aquí.
            time_obj = None
            formatos_posibles = ["%I:%M %p", "%I:%M%p"]

            for fmt in formatos_posibles:
                try:
                    time_obj = datetime.strptime(clean_time, fmt).time()
                    break
                except ValueError:
                    continue

            if time_obj is None:
                return None

            # 3. Determinar Año
            now = datetime.now()

            if explicit_year:
                # Si el cine ya nos dio el año (ej: "del 2025"), usamos ese.
                year = explicit_year
                dt_obj = datetime(year, month, day, time_obj.hour, time_obj.minute)
            else:
                # Lógica Dinámica (90 días)
                year = now.year
                dt_obj = datetime(year, month, day, time_obj.hour, time_obj.minute)

                # Si la fecha parece muy antigua (ej: Enero cuando estamos en Diciembre), es año siguiente
                if dt_obj < (now - timedelta(days=90)):
                    dt_obj = dt_obj.replace(year=year + 1)

            # 4. Filtro Medianoche (Para no guardar eventos pasados del día anterior)
            midnight_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

            if dt_obj >= midnight_today:
                return dt_obj

            return None

        except (ValueError, IndexError, AttributeError):
            return None
