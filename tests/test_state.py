"""
Tests unitarios para el Estado de la Aplicación (Frontend Logic).

Este módulo verifica la lógica de negocio que reside en el State de Reflex.
Se prueban dos aspectos principales:
1. Propiedades computadas (@rx.var): Transformación de datos (agrupación por cine).
2. Manejo de eventos (@rx.event): Carga de datos, manejo de errores y estados de carga (spinners).

Nota: Se utilizan Mocks para aislar el estado de la base de datos real.
"""

from datetime import datetime

from sqlmodel import Session

from agenda_cultural.backend import Movie
from agenda_cultural.state import State


def test_movies_by_center_groups_correctly(mocker):
    """
    Verifica que la propiedad computada 'movies_by_center' agrupe correctamente
    las películas por su centro cultural y maneje listas vacías.
    """
    # === ARRANGE (Preparar) ===
    # 1. Mockeamos la función externa que define qué cines existen.
    # Esto aísla el test de cambios en la configuración global.
    mocker.patch(
        "agenda_cultural.state.get_all_center_keys",
        return_value=["alianza_francesa", "lum", "ccpucp"],
    )

    state = State()

    # Caso A: Cine con 1 película
    movie_af = Movie(
        title="El evangelio...",
        location="AF",
        date=datetime(2026, 4, 12),
        center="alianza_francesa",
    )

    # Caso B: Cine con 2 películas (Prueba de agrupación/append)
    movie_lum_1 = Movie(
        title="Inception", location="LUM", date=datetime(2016, 6, 29), center="lum"
    )
    movie_lum_2 = Movie(
        title="Interstellar", location="LUM", date=datetime(2016, 6, 30), center="lum"
    )

    # Inyectamos datos manualmente al estado (simulando que ya se cargaron)
    state.movies = [movie_af, movie_lum_1, movie_lum_2]

    # === ACT (Ejecutar) ===
    # Accedemos a la propiedad para disparar el cálculo
    result = state.movies_by_center

    # === ASSERT (Verificar) ===

    # 1. Verificar agrupación simple
    assert len(result["alianza_francesa"]) == 1
    assert result["alianza_francesa"][0].title == "El evangelio..."

    # 2. Verificar agrupación múltiple (que no se sobrescriban)
    assert len(result["lum"]) == 2
    assert result["lum"][0].title == "Inception"
    assert result["lum"][1].title == "Interstellar"

    # 3. Verificar manejo de cines sin películas (debe ser lista vacía, no error)
    assert result["ccpucp"] == []


def test_load_movies_with_movies_in_db(session: Session, mocker):
    """
    Happy Path: Verifica que load_movies cargue datos de la DB al estado
    y apague el indicador de carga (is_loading).
    """
    # === ARRANGE ===
    # Mockeamos rx.session en el módulo 'state' para interceptar la conexión
    mocker_rx_session = mocker.patch("agenda_cultural.state.rx.session")
    mocker_rx_session.return_value.__enter__.return_value = session

    # Insertamos datos en la DB simulada
    existing_movie = Movie(
        title="Avatar",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 18, 0),
        url="http://example.com/avatar",
    )
    session.add(existing_movie)
    session.commit()

    state = State()

    # === ACT ===
    # Ejecutamos el evento. Ignoramos type checking porque Reflex trata los
    # eventos de manera especial, pero en unit tests se llaman como métodos.
    state.load_movies()  # ty: ignore[call-non-callable]

    # === ASSERT ===
    assert len(state.movies) == 1
    assert state.is_loading is False


def test_load_movies_without_movies_in_db(session: Session, mocker):
    """
    Edge Case: Verifica que el sistema maneje correctamente una base de datos vacía
    (sin errores y apagando el loading).
    """
    # === ARRANGE ===
    mocker_rx_session = mocker.patch("agenda_cultural.state.rx.session")
    mocker_rx_session.return_value.__enter__.return_value = session

    state = State()

    # === ACT ===
    state.load_movies()  # ty: ignore[call-non-callable]

    # === ASSERT ===
    assert state.movies == []
    assert state.is_loading is False


def test_load_movies_exception(mocker):
    """
    Sad Path: Verifica la resiliencia del sistema ante fallos de conexión.
    La app NO debe crashear, debe loguear el error y apagar el loading.
    """
    # === ARRANGE ===
    # 1. Simulamos fallo crítico (Connection Error)
    mock_rx_session = mocker.patch("agenda_cultural.state.rx.session")
    mock_rx_session.side_effect = Exception("Conexión perdida con la Base de Datos")

    # 2. Espiamos el logger para asegurar que el error no sea silenciado
    mock_logger = mocker.patch("agenda_cultural.state.db_logger")

    state = State()

    # === ACT ===
    state.load_movies()  # ty: ignore[call-non-callable]

    # === ASSERT ===
    # La lista debe quedar limpia (empty safe list)
    assert state.movies == []
    # El spinner debe desaparecer gracias al bloque 'finally'
    assert state.is_loading is False
    # El error debió quedar registrado en los logs
    mock_logger.error.assert_called_once()
