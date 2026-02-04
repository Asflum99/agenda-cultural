import pytest

from agenda_cultural.backend.scrapers.bnp.scraper import BnpScraper


@pytest.fixture
def scraper():
    """Retorna una instancia limpia de BnpScraper para cada test."""
    return BnpScraper()


@pytest.mark.parametrize(
    "input_text, expected",
    [
        (
            "Hall principal, Biblioteca Nacional del Perú, Av. De La Poesía 160, San Borja",
            "Biblioteca Nacional del Perú - Av. De La Poesía 160 (San Borja)",
        ),
        (
            "Anfiteatro, Biblioteca Nacional del Perú, Av. De La Poesía 160, San Borja",
            "Biblioteca Nacional del Perú - Av. De La Poesía 160 (San Borja)",
        ),
        (
            "Anfiteatro, BNP, Av. De La Poesía 160, San Borja",
            "BNP - Av. De La Poesía 160 (San Borja)",
        ),
        (
            "Biblioteca Nacional del Perú, Av. De La Poesía 160, San Borja",
            "Biblioteca Nacional del Perú - Av. De La Poesía 160 (San Borja)",
        ),
        (
            "Hall Principal, Av. De La Poesía 160, San Borja",
            "Hall Principal, Av. De La Poesía 160, San Borja",
        ),
    ],
)
def test_clean_location(scraper, input_text, expected):
    assert scraper._clean_location(input_text) == expected


@pytest.mark.parametrize(
    "input_text, expected_day, expected_month_str, expected_year, expected_time_str",
    [
        # Happy path completo
        ("Sábado, 14 de Febrero del 2026 6:30PM", 14, "Febrero", 2026, "6:30PM"),
        # Sin "del" antes del año
        ("14 de abril 2026 6:30pm", 14, "abril", 2026, "6:30pm"),
        # Con espacio antes de AM/PM
        ("14 de mayo del 2026 6:30 pm", 14, "mayo", 2026, "6:30pm"),
        # Hora con cero inicial
        ("14 de junio del 2026 06:45pm", 14, "junio", 2026, "6:45pm"),
        # Días extremos (bordes del calendario)
        ("31 de enero del 2026 12:00PM", 31, "enero", 2026, "12:00PM"),
        ("1 de julio del 2026 12:00AM", 1, "julio", 2026, "12:00AM"),
        # Setiembre vs Septiembre
        ("10 de setiembre del 2026 6:00pm", 10, "setiembre", 2026, "6:00pm"),
    ],
)
def test_parse_date(
    scraper,
    input_text,
    expected_day,
    expected_month_str,
    expected_year,
    expected_time_str,
):
    result = scraper._parse_date(input_text)
    assert result is not None
    day, month_str, year, time_str = result
    assert day == expected_day
    assert month_str == expected_month_str
    assert year == expected_year
    assert time_str == expected_time_str


def test_parse_date_invalid(scraper):
    """Test que verifica que retorna None cuando no encuentra una fecha válida."""
    assert scraper._parse_date("Texto sin fecha válida") is None
    assert scraper._parse_date("") is None
    assert scraper._parse_date("15 de MesInvalido del 2026 6:30pm") is None
    assert scraper._parse_date("0 de febrero del 2026 6:30pm") is None


@pytest.mark.parametrize(
    "input_text, expected_title, expected_year",
    [
        # Happy path: título con año
        ("Flow (2024)", "Flow", "2024"),
        # Título sin año
        ("La La Land", "La La Land", None),
        # Título con caracteres especiales (acentos, eñes)
        ("El Señor de los Anillos (2001)", "El Señor de los Anillos", "2001"),
        # Título con números (pero no es el año de estreno)
        ("Se7en (1995)", "Se7en", "1995"),
        # Título que incluye un año (distinguir del año de estreno)
        ("1917 (2019)", "1917", "2019"),
    ],
)
def test_parse_title_and_year(scraper, input_text, expected_title, expected_year):
    """Test que verifica la extracción de título y año de diferentes formatos."""
    result = scraper._parse_title_and_year(input_text)
    assert result is not None
    title, year = result
    assert title == expected_title
    assert year == expected_year


def test_parse_title_and_year_invalid(scraper):
    """Test que verifica que retorna None cuando no encuentra un título válido."""
    # String vacío
    assert scraper._parse_title_and_year("") is None
    # Solo espacios
    assert scraper._parse_title_and_year("   ") is None
