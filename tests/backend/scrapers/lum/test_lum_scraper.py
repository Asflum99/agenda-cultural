"""
Suite de pruebas unitarias para el Scraper del LUM (Lugar de la Memoria).
Se enfoca en validar la lógica atómica de limpieza de texto, parsing de fechas
y heurísticas de identificación de títulos en párrafos.
"""

import pytest

from agenda_cultural.backend.scrapers.lum.scraper import LumScraper


@pytest.fixture
def scraper():
    """Retorna una instancia fresca de LumScraper para cada test."""
    return LumScraper()


# =================================================================
# PRUEBAS DE LIMPIEZA Y EXTRACCIÓN (Regex)
# =================================================================


@pytest.mark.parametrize(
    "input_text, expected",
    [
        # Caso 1: Comillas tipográficas y año
        ("“La teta asustada” (2009)", "La teta asustada"),
        # Caso 2: Comilas rectas y espacios
        ('"Asu Mare" ', "Asu Mare"),
        # Caso 3: Prefijo de categoría con dos puntos
        ("Cinefórum: El limpiador", "El limpiador"),
        # Caso 4: Prefijo "Proyección" y metadatos de duración
        ("Proyección: Wiñaypacha (94. min)", "Wiñaypacha"),
        # Caso 5: Título con nombre del director (Uso de DIRECTOR_PATTERN)
        ("Manco Cápac, de Henry Vallejo", "Manco Cápac"),
        # Caso 6: Título "sucio" con puntos y comas al final
        ("Documental: Identidad...", "Identidad"),
    ],
)
def test_clean_title(scraper, input_text, expected):
    """Valida la limpieza de ruido (prefijos, años, directores) en los títulos."""
    assert scraper._clean_title(input_text) == expected


@pytest.mark.parametrize(
    "date_text, expected_day, expected_month",
    [
        # Validación de insensibilidad a mayúsculas (Case-insensitive)
        ("13 de Enero", 13, "enero"),
        # Validación de días con cero inicial y texto en minúsculas
        ("05 de mayo", 5, "mayo"),
        # Texto extra al inicio (Debe encontrar la fecha aunque no sea el inicio)
        ("martes 20 de agosto", 20, "agosto"),
        # Manejo de espacios en blanco (Padding)
        (" 2 de Diciembre ", 2, "diciembre"),
    ],
)
def test_parse_lum_date_string(scraper, date_text, expected_day, expected_month):
    """Prueba la extracción de día y mes desde cadenas de texto variables."""
    day, month = scraper._parse_lum_date_string(date_text)
    assert day == expected_day
    assert month == expected_month


@pytest.mark.parametrize(
    "text, expected",
    [
        ("(2024)", True),  # Año estándar
        ("(94 min.)", True),  # Duración con punto
        ("(120 min)", True),  # Duración sin punto
        ("(1998) 90 min.", True),  # Ambos metadatos juntos
        ("Película (2000)", True),  # Texto antes del metadato
        ("Sala 1", False),  # Solo número, sin paréntesis
        ("(Enero)", False),  # Texto en paréntesis, pero no año/min
        ("2024", False),  # Año sin paréntesis
        ("()", False),  # Paréntesis vacíos
        ("", False),  # String vacío
        ("Mañana a las 19:00", False),  # Horas (no deben confundirse con duración)
    ],
)
def test_has_technical_metadata_logic(scraper, text, expected):
    """Valida que la detección de fichas técnicas sea precisa y evite falsos positivos."""
    assert scraper._has_technical_metadata(text) == expected


# =================================================================
# PRUEBAS DE LÓGICA DE ÍNDICES (Heurísticas)
# =================================================================


@pytest.mark.parametrize(
    "lines, expected_index",
    [
        # Regla 1: Metadata en la misma línea
        (["Cine: Wiñaypacha (2017)"], 0),
        # Regla 2: Título explícito después de ':'
        (["Proyección: Wiñaypacha", "(2017) 86 min."], 0),
        # Regla 3: Metadata abajo confirma que el título es la línea actual
        (["Película", "(2022) 110 min.", "20 de Enero"], 0),
        # Regla 4: El título real está en la siguiente línea con comillas
        (["Cine en el LUM:", "“Juliana”", "(1988)"], 1),
        # Fallback: Solo tenemos la palabra clave como referencia
        (["Cinefórum", "Charla debate", "21 de Enero"], 0),
        # Estrategia estructural: Comillas + Metadatos (sin palabras clave)
        (["“La teta asustada”", "(2009) 94 min."], 0),
        # Casos Negativos: El párrafo no contiene cine
        (["Conversatorio de literatura", "Sala de grado"], -1),
    ],
)
def test_resolve_title_index(scraper, lines, expected_index):
    """Valida la jerarquía de decisión para encontrar el título en párrafos complejos."""
    assert scraper._resolve_title_index(lines) == expected_index


@pytest.mark.parametrize(
    "lines, start_index, expected_index",
    [
        # Caso 1: Ubicación estándar debajo del título/meta
        (["“Juliana”", "(1988) 92 min.", "15 de Agosto", "6:00 p.m."], 1, 2),
        # Caso 2: Manejo de errores de límites
        (["“Juliana”", "15 de Agosto"], 5, -1),
        # Caso 3: Filtrado de falsos positivos (mes sin número)
        (["Ciclo de Cine: Enero", "“Juliana”", "15 de Enero"], 0, 2),
        # Caso 4: Filtrado de falsos positivos (número sin mes)
        (["Sala 1", "“Juliana”", "15 de Enero"], 0, 2),
        # Caso 5: Continuidad (ignorar fechas previas al start_index)
        (["10 de Mayo", "“La teta asustada”", "25 de Mayo"], 1, 2),
        # Caso 6: Ausencia de datos
        (["Texto genérico", "Sin números ni meses"], 0, -1),
    ],
)
def test_resolve_date_index(scraper, lines, start_index, expected_index):
    """Verifica que el buscador de fechas respete el punto de inicio y valide mes+día."""
    assert scraper._resolve_date_index(lines, start_index) == expected_index
