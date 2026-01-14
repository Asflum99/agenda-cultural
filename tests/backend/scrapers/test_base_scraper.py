"""
Tests unitarios para la lógica base de los Scrapers.

Este módulo verifica `ScraperInterface`, enfocándose en la utilidad
`validate_and_build_date`. Se prueban:
1. Inferencia de años (actual, explícito y cambio de año).
2. Filtrado de eventos pasados.
3. Resiliencia ante datos sucios y tipos de datos incorrectos.
"""

from datetime import datetime

from freezegun import freeze_time

from agenda_cultural.backend import Movie
from agenda_cultural.backend.scrapers.base_scraper import ScraperInterface

# === HELPER CLASSES ===


class DummyScraper(ScraperInterface):
    """
    Clase concreta mínima para poder instanciar y testear
    los métodos de la clase abstracta ScraperInterface.
    """

    async def get_movies(self) -> list[Movie]:
        return []


# === SECCIÓN 1: LÓGICA DE CALENDARIO E INFERENCIA ===


@freeze_time("2025-01-01 10:00:00")
def test_validate_date_explicit_year():
    """
    Happy Path: La web nos da el año explícito.
    Verifica que se respete el año provisto y no se use el actual.
    """
    scraper = DummyScraper()
    # Usamos un año futuro (2030) relativo al tiempo congelado (2025)
    result = scraper.validate_and_build_date(15, "Enero", "7:00 pm", 2030)

    assert result is not None
    assert result == datetime(2030, 1, 15, 19, 0)


@freeze_time("2026-06-01 10:00:00")
def test_validate_date_implicit_year():
    """
    Happy Path: La web NO da el año.
    Verifica que se asuma el año actual (congelado en 2026).
    """
    scraper = DummyScraper()
    result = scraper.validate_and_build_date(15, "Junio", "8:00 pm")

    assert result is not None
    assert result == datetime(2026, 6, 15, 20, 0)


@freeze_time("2025-12-20 10:00:00")
def test_validate_date_year_turnover():
    """
    Edge Case: Estamos a finales de año (Dic 2025) y el evento es en Enero.
    Verifica que la lógica detecte que el evento pertenece al año siguiente (2026).
    """
    scraper = DummyScraper()
    result = scraper.validate_and_build_date(5, "Enero", "10:00 am")

    assert result is not None
    assert result.year == 2026
    assert result.month == 1
    assert result.day == 5


# === SECCIÓN 2: REGLAS DE NEGOCIO ===


@freeze_time("2026-01-15 10:00:00")
def test_validate_date_past_event():
    """
    Si el evento ocurrió antes de hoy, se debe descartar.
    Hoy es 15, evento fue el 14 -> Debe retornar None.
    """
    scraper = DummyScraper()
    result = scraper.validate_and_build_date(14, "Enero", "10:00 am")

    assert result is None


# === SECCIÓN 3: MANEJO DE ERRORES Y RESILIENCIA ===


def test_validate_date_invalid_inputs():
    """
    Entradas de texto sin sentido (meses falsos, horas rotas)
    deben ser manejadas retornando None, sin lanzar excepciones.
    """
    scraper = DummyScraper()

    # Caso 1: Mes inexistente
    res1 = scraper.validate_and_build_date(10, "NoSoyUnMes", "7pm")
    assert res1 is None

    # Caso 2: Hora incomprensible
    res2 = scraper.validate_and_build_date(10, "Enero", "Hora de cenar")
    assert res2 is None


def test_validate_date_handles_value_error():
    """
    Exception Handling (ValueError):
    Simula una fecha que es 'texto válido' pero 'calendario imposible' (Ej: 32 Ene).
    El scraper debe atrapar el ValueError interno y retornar None.
    """
    scraper = DummyScraper()
    result = scraper.validate_and_build_date(32, "Enero", "7:00 pm", 2026)

    assert result is None


def test_validate_date_handles_attribute_error():
    """
    Exception Handling (AttributeError):
    Simula pasar un objeto que no tiene los métodos de string esperados (.replace, .upper).
    Ej: Pasar un entero en 'time_str'.
    """
    scraper = DummyScraper()
    # Forzamos un entero donde se espera string
    result = scraper.validate_and_build_date(
        15,
        "Enero",
        12345,  # ty: ignore[invalid-argument-type]
    )
    assert result is None


def test_validate_date_handles_type_error():
    """
    Exception Handling (TypeError):
    Simula pasar un tipo de dato incorrecto al constructor de datetime.
    Ej: Pasar el día como string "15" en lugar de int 15.
    """
    scraper = DummyScraper()
    # Forzamos string donde se espera int
    result = scraper.validate_and_build_date(
        "15",  # ty: ignore[invalid-argument-type]
        "Enero",
        "7:00 pm",
    )
    assert result is None
