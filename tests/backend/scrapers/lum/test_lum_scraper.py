"""
Tests unitarios para el Scraper del LUM (Lugar de la Memoria).

Esta suite valida la lógica "offline" del scraper, asegurando que las funciones
de limpieza, extracción de fechas, heurísticas de detección de títulos
y ensamblaje de objetos funcionen correctamente ante diversas variaciones
de texto, sin necesidad de conectar con un navegador real.
"""

from datetime import datetime

import pytest
from freezegun import freeze_time

from agenda_cultural.backend.scrapers.lum.scraper import LumScraper


@pytest.fixture
def scraper():
    """Retorna una instancia fresca de LumScraper para cada test."""
    return LumScraper()


# ==============================================================================
#  BLOQUE 1: LIMPIEZA Y PARSING DE TEXTO (ATÓMICO)
#  Pruebas de funciones puras que transforman strings.
# ==============================================================================


@pytest.mark.parametrize(
    "input_text, expected",
    [
        # --- Limpieza de Caracteres ---
        ("“La teta asustada” (2009)", "La teta asustada"),  # Quitar comillas y año
        ('"Asu Mare" ', "Asu Mare"),  # Quitar comillas rectas y trim
        # --- Prefijos de Categoría ---
        ("Cinefórum: El limpiador", "El limpiador"),
        ("Proyección: Wiñaypacha (94. min)", "Wiñaypacha"),  # Prefijo + Metadata
        ("Documental: Identidad...", "Identidad"),  # Puntuación final excesiva
        # --- Patrones de Director ---
        ("Manco Cápac, de Henry Vallejo", "Manco Cápac"),
    ],
)
def test_clean_title(scraper, input_text, expected):
    """
    Valida la limpieza de ruido en los títulos de películas.
    Es crucial eliminar años, directores y prefijos para aumentar
    la tasa de éxito en la búsqueda posterior en la API de TMDB.
    """
    assert scraper._clean_title(input_text) == expected


@pytest.mark.parametrize(
    "date_text, expected_day, expected_month",
    [
        # --- Variaciones de Formato ---
        ("13 de Enero", 13, "enero"),  # Caso estándar
        ("05 de mayo", 5, "mayo"),  # Cero inicial (padding) + minúscula
        ("martes 20 de agosto", 20, "agosto"),  # Día de la semana incluido
        (" 2 de Diciembre ", 2, "diciembre"),  # Espacios en blanco extremos
    ],
)
def test_parse_lum_date_string(scraper, date_text, expected_day, expected_month):
    """
    Prueba la extracción robusta de día y mes desde texto natural.
    Debe ser tolerante a mayúsculas, ceros a la izquierda y palabras extra.
    """
    day, month = scraper._parse_lum_date_string(date_text)
    assert day == expected_day
    assert month == expected_month


@pytest.mark.parametrize(
    "text, expected",
    [
        # --- Casos Positivos (Es metadata) ---
        ("(2024)", True),  # Año estándar
        ("(94 min.)", True),  # Duración
        ("(1998) 90 min.", True),  # Combinado
        ("Película (2000)", True),  # Texto + Metadata (heurística flexible)
        # --- Casos Negativos (Es título u otra cosa) ---
        ("Sala 1", False),  # Número de sala (parece año/duración pero no es)
        ("(Enero)", False),  # Texto entre paréntesis
        ("2024", False),  # Año suelto sin contexto de paréntesis
        ("Mañana a las 19:00", False),  # Horas (conflicto potencial con duración)
        ("", False),  # Vacío
    ],
)
def test_has_technical_metadata_logic(scraper, text, expected):
    """
    Valida la detección de líneas que contienen ficha técnica (Año/Duración).
    Esta función es vital para distinguir si una línea es un título de película
    o simplemente información técnica sobre la proyección.
    """
    assert scraper._has_technical_metadata(text) == expected


# ==============================================================================
#  BLOQUE 2: HEURÍSTICAS DE ESTRUCTURA (LOGIC DE PÁRRAFO)
#  Pruebas que determinan qué línea es qué dentro de un bloque de texto.
# ==============================================================================


@pytest.mark.parametrize(
    "lines, expected_index",
    [
        # Regla 1: Metadata en la misma línea -> Título está ahí mismo.
        (["Cine: Wiñaypacha (2017)"], 0),
        # Regla 2: Título explícito tras prefijo "Proyección:"
        (["Proyección: Wiñaypacha", "(2017) 86 min."], 0),
        # Regla 3: Metadata en línea siguiente confirma al título arriba.
        (["Película", "(2022) 110 min.", "20 de Enero"], 0),
        # Regla 4: "Sandwich". Título entre palabra clave y metadata.
        (["Cine en el LUM:", "“Juliana”", "(1988)"], 1),
        # Fallback 1: Comillas + Metadatos (sin palabras clave como "Cine").
        (["“La teta asustada”", "(2009) 94 min."], 0),
        # Casos Negativos: El párrafo no parece tener película.
        (["Conversatorio de literatura", "Sala de grado"], -1),
    ],
)
def test_resolve_title_index(scraper, lines, expected_index):
    """
    Valida la jerarquía de decisión para encontrar el título en párrafos complejos.
    Prueba que el scraper priorice las reglas más específicas antes que las genéricas.
    """
    assert scraper._resolve_title_index(lines) == expected_index


@pytest.mark.parametrize(
    "lines, start_index, expected_index",
    [
        # Caso Ideal: Fecha debajo del título/meta.
        (["“Juliana”", "(1988) 92 min.", "15 de Agosto", "6:00 p.m."], 1, 2),
        # Manejo de error: Índice de inicio fuera de rango.
        (["“Juliana”", "15 de Agosto"], 5, -1),
        # Falsos Positivos: Ignorar textos que parecen fechas parcialmente.
        (
            ["Ciclo de Cine: Enero", "“Juliana”", "15 de Enero"],
            0,
            2,
        ),  # "Enero" solo no basta
        (["Sala 1", "“Juliana”", "15 de Enero"], 0, 2),  # "1" solo no basta
        # Continuidad: Ignorar fechas que están ANTES del título (start_index).
        (["10 de Mayo", "“La teta asustada”", "25 de Mayo"], 1, 2),
        # Caso Negativo: No hay fecha.
        (["Texto genérico", "Sin números ni meses"], 0, -1),
    ],
)
def test_resolve_date_index(scraper, lines, start_index, expected_index):
    """
    Verifica que el buscador de fechas respete el orden de lectura.
    Solo debe buscar fechas DESPUÉS de donde se encontró el título (start_index).
    """
    assert scraper._resolve_date_index(lines, start_index) == expected_index


# ==============================================================================
#  BLOQUE 3: VALIDACIÓN DE AGENDA (BUSINESS LOGIC)
#  Pruebas temporales usando freeze_time para validar vigencia.
# ==============================================================================


@freeze_time("2025-05-15")
def test_is_relevant_monthly_agenda_future_month(scraper):
    """Happy Path: La agenda es de un mes futuro (Junio) vs Hoy (Mayo). -> True"""
    title = "agenda junio 2025"
    assert scraper._is_relevant_monthly_agenda(title) is True


@freeze_time("2025-05-15")
def test_is_relevant_monthly_agenda_current_month(scraper):
    """Happy Path: La agenda es del mes actual. -> True"""
    title = "agenda mayo 2025"
    assert scraper._is_relevant_monthly_agenda(title) is True


@freeze_time("2025-05-15")
def test_is_relevant_monthly_agenda_past_month(scraper):
    """Filtro: La agenda es del mes pasado (Abril). -> False"""
    title = "agenda abril 2025"
    assert scraper._is_relevant_monthly_agenda(title) is False


@freeze_time("2025-05-15")
def test_is_relevant_monthly_agenda_past_year(scraper):
    """Filtro: El mes es igual (Mayo) pero del año pasado (2024). -> False"""
    title = "agenda mayo 2024"
    assert scraper._is_relevant_monthly_agenda(title) is False


@freeze_time("2025-05-15")
def test_is_relevant_monthly_agenda_case_insensitive(scraper):
    """Debe detectar el mes aunque esté en MAYÚSCULAS."""
    title = "AGENDA MAYO 2025"
    assert scraper._is_relevant_monthly_agenda(title) is True


# --- Casos de Error de Formato ---


def test_is_relevant_monthly_agenda_no_year_in_title(scraper):
    """Edge Case: Título tiene mes pero no año (no podemos saber si es vigente)."""
    title = "agenda enero"
    assert scraper._is_relevant_monthly_agenda(title) is False


def test_is_relevant_monthly_agenda_no_month_in_title(scraper):
    """Edge Case: Título tiene año pero no mes."""
    title = "agenda 2025"
    assert scraper._is_relevant_monthly_agenda(title) is False


# ==============================================================================
#  BLOQUE 4: ENSAMBLAJE DE PELÍCULA (INTEGRACIÓN)
#  Pruebas de la función _build_movie_from_lines, mockeando APIs externas.
# ==============================================================================


@freeze_time("2025-10-10 10:00:00")
def test_build_movie_from_lines_happy_path(scraper, mocker):
    """
    Happy Path:
    - Se extraen datos válidos (Título, Fecha, Hora).
    - Se infiere el año correcto (2026 siendo Oct 2025).
    - La API de pósters responde con una URL válida.
    """
    mocker_get_movie_poster = mocker.patch(
        "agenda_cultural.backend.scrapers.lum.scraper.get_movie_poster"
    )
    mocker_get_movie_poster.return_value = "poster_url"

    lines = ["Cine: Alien", "bla bla", "20 de enero", "8:00 pm"]
    title_index = 0
    date_index = 2
    source_url = "source_url_random"

    result = scraper._build_movie_from_lines(lines, title_index, date_index, source_url)

    assert result.title == "Alien"
    assert result.location == "Lugar de la Memoria - Bajada San Martín 151 (Miraflores)"
    assert result.center == "lum"
    assert result.date == datetime(2026, 1, 20, 20, 0)
    assert result.poster_url == "poster_url"
    assert result.source_url == "source_url_random"


@freeze_time("2025-10-10 11:00:00")
def test_build_movie_returns_none_on_invalid_date(scraper):
    """
    Filtro de Validez:
    - La línea de fecha no contiene información válida.
    - validate_and_build_date falla internamente.
    - Se debe retornar None y no crashear.
    """
    lines = ["Cine: Alien", "bla bla", "20", "8:00 pm"]
    title_index = 0
    date_index = 2
    source_url = "source_url_random"

    result = scraper._build_movie_from_lines(lines, title_index, date_index, source_url)

    assert result is None


@freeze_time("2025-10-10 10:00:00")
def test_build_movie_handles_missing_poster_gracefully(scraper, mocker):
    """
    Resiliencia:
    - Todo es válido, pero la API externa de pósters falla (retorna None).
    - La película DEBE crearse igualmente, con poster_url=None.
    """
    mocker_get_movie_poster = mocker.patch(
        "agenda_cultural.backend.scrapers.lum.scraper.get_movie_poster"
    )
    mocker_get_movie_poster.return_value = None  # Simula fallo de API

    lines = ["Cine: Alien", "bla bla", "20 de enero", "8:00 pm"]
    title_index = 0
    date_index = 2
    source_url = "source_url_random"

    result = scraper._build_movie_from_lines(lines, title_index, date_index, source_url)

    assert result.title == "Alien"
    assert result.location == "Lugar de la Memoria - Bajada San Martín 151 (Miraflores)"
    assert result.center == "lum"
    assert result.date == datetime(2026, 1, 20, 20, 0)
    assert result.poster_url is None
    assert result.source_url == "source_url_random"
