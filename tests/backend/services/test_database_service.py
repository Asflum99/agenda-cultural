"""
Tests unitarios y de integración para el servicio de base de datos.

Este módulo verifica la lógica de persistencia de datos, asegurando que:
1. No se inserten duplicados (idempotencia).
2. Se limpien registros antiguos correctamente.
3. La sincronización maneje tanto bases de datos vacías como pobladas.

Se utiliza una base de datos SQLite en memoria para aislar los tests del archivo real.
"""

from datetime import datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from agenda_cultural.backend.models import Movie
from agenda_cultural.backend.services.database_service import (
    _filter_new_movies,
    cleanup_past_movies,
    sync_movies_to_db,
)


@pytest.fixture(name="session")
def session_fixture():
    """
    Crea una base de datos SQLite temporal en memoria RAM.

    Esta fixture se ejecuta antes de cada test, entregando una sesión limpia.
    Al finalizar el test, la base de datos se destruye automáticamente.
    """
    # Usamos 3 barras '///' para indicar una ruta relativa en memoria
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=None
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def test_filter_new_movies_excludes_duplicates(session: Session):
    """
    Verifica que la función auxiliar _filter_new_movies detecte correctamente
    las películas que ya existen en la BD basándose en (Cine, Título, Fecha).
    """
    # === ARRANGE (Preparar) ===
    # 1. Insertamos una película "base" en la BD
    existing_movie = Movie(
        title="Avatar",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 18, 0),
        url="http://example.com/avatar",
    )
    session.add(existing_movie)
    session.commit()

    # 2. Preparamos los datos "scrapeados"
    # Una película totalmente nueva
    new_movie = Movie(
        title="Shrek",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 20, 0),
        url="http://example.com/shrek",
    )
    # Una copia exacta de la que ya existe (mismos datos clave)
    duplicate_movie = Movie(
        title="Avatar",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 18, 0),
        url="http://example.com/avatar",
    )

    scraped_movies = [duplicate_movie, new_movie]

    # === ACT (Ejecutar) ===
    # Filtramos la lista sucia
    result = _filter_new_movies(scraped_movies, session)

    # === ASSERT (Verificar) ===
    # Solo debería quedar "Shrek". "Avatar" debe ser descartada.
    assert len(result) == 1
    assert result[0].title == "Shrek"
    assert result[0].title != "Avatar"


def test_cleanup_past_movies(session: Session, mocker):
    """
    Verifica que se eliminen las películas anteriores a la fecha actual
    y se conserven las futuras.
    """
    # === ARRANGE (Preparar) ===
    # Mockeamos rx.session para que NO use la BD real, sino nuestra fixture 'session'
    mocker_rx_session = mocker.patch(
        "agenda_cultural.backend.services.database_service.rx.session"
    )
    # Truco para mockear un Context Manager (el 'with ... as session'):
    mocker_rx_session.return_value.__enter__.return_value = session

    # Película del pasado (Año 2000) -> Debería borrarse
    past_movie = Movie(
        title="Toy Story",
        location="lum",
        center="LUM",
        date=datetime(2000, 2, 15, 18, 0),
        url="http://example.com/toy-story",
    )
    # Película del futuro (Año 3000) -> Debería quedarse
    future_movie = Movie(
        title="Robopocalipsis",
        location="ccpucp",
        center="CCPUCP",
        date=datetime(3000, 5, 12, 19, 0),
        url="http://example.com/robopocalipsis",
    )

    session.add(past_movie)
    session.add(future_movie)
    session.commit()

    # === ACT (Ejecutar) ===
    cleanup_past_movies()

    # === ASSERT (Verificar) ===
    result = session.exec(select(Movie)).all()

    # Solo debe quedar 1 película y debe ser la del futuro
    assert len(result) == 1
    assert result[0].date == datetime(3000, 5, 12, 19, 0)


def test_sync_movies_to_db_without_movies(session: Session, mocker):
    """
    Prueba de Carga Inicial: Verifica que si la BD está vacía,
    todas las películas scrapeadas se guarden correctamente.
    """
    # === ARRANGE ===
    mocker_rx_session = mocker.patch(
        "agenda_cultural.backend.services.database_service.rx.session"
    )
    mocker_rx_session.return_value.__enter__.return_value = session

    new_movie_1 = Movie(
        title="Shrek",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 20, 0),
        url="http://example.com/shrek",
    )
    new_movie_2 = Movie(
        title="Avatar",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 18, 0),
        url="http://example.com/avatar",
    )
    scraped_movies = [new_movie_1, new_movie_2]

    # === ACT ===
    sync_movies_to_db(scraped_movies)

    # === ASSERT ===
    result = session.exec(select(Movie)).all()
    titles = [m.title for m in result]

    # Ambas deben haberse guardado
    assert len(result) == 2
    assert "Shrek" in titles
    assert "Avatar" in titles


def test_sync_movies_to_db_with_movies(session: Session, mocker):
    """
    Prueba de Sincronización Incremental: Verifica que si ya existen datos,
    solo se agreguen las películas nuevas y se respeten las existentes.
    """
    # === ARRANGE ===
    mocker_rx_session = mocker.patch(
        "agenda_cultural.backend.services.database_service.rx.session"
    )
    mocker_rx_session.return_value.__enter__.return_value = session

    # 1. Estado inicial: Avatar ya existe
    existing_movie = Movie(
        title="Avatar",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 18, 0),
        url="http://example.com/avatar",
    )
    session.add(existing_movie)
    session.commit()

    # 2. Input del scraper: Avatar (repetida) y Shrek (nueva)
    new_movie = Movie(
        title="Shrek",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 20, 0),
        url="http://example.com/shrek",
    )
    duplicate_movie = Movie(
        title="Avatar",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 18, 0),
        url="http://example.com/avatar",
    )
    scraped_movies = [new_movie, duplicate_movie]

    # === ACT ===
    sync_movies_to_db(scraped_movies)

    # === ASSERT ===
    result = session.exec(select(Movie)).all()
    titles = [m.title for m in result]

    # El resultado final debe ser 2 películas únicas (Avatar y Shrek)
    # No 3 (que implicaría duplicados) ni 1 (que implicaría borrado accidental)
    assert len(result) == 2
    assert "Shrek" in titles
    assert "Avatar" in titles


def test_sync_movies_respects_different_dates_and_centers(session: Session, mocker):
    """
    Verifica que el sistema NO considere duplicado si cambia la fecha o el cine,
    aunque el título sea el mismo.
    """
    # === ARRANGE ===
    mocker_rx_session = mocker.patch(
        "agenda_cultural.backend.services.database_service.rx.session"
    )
    mocker_rx_session.return_value.__enter__.return_value = session

    # 1. Ya existe "Batman" hoy a las 6pm
    batman_base = Movie(
        title="Batman",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 18, 0),
        url="http://example.com/batman1",
    )
    session.add(batman_base)
    session.commit()

    # 2. El scraper trae "Batman" otra vez, pero a las 9pm
    batman_late_show = Movie(
        title="Batman",
        location="cineplanet",
        center="Cineplanet",
        date=datetime(2026, 1, 20, 21, 0),
        url="http://example.com/batman2",
    )

    # 3. Y trae "Batman" a la misma hora pero en OTRO cine
    batman_other_cinema = Movie(
        title="Batman",
        location="cinemark",
        center="Cinemark",
        date=datetime(2026, 1, 20, 18, 0),
        url="http://example.com/batman3",
    )

    scraped_movies = [batman_late_show, batman_other_cinema]

    # === ACT ===
    sync_movies_to_db(scraped_movies)

    # === ASSERT ===
    result = session.exec(select(Movie)).all()

    # Deberíamos tener 3 Batmans distintos en la base de datos
    assert len(result) == 3

    # Verificamos fechas para asegurarnos
    dates = [m.date.hour for m in result]
    assert 18 in dates
    assert 21 in dates


def test_sync_movies_empty_input_does_nothing(session: Session, mocker):
    """
    Verifica que si el scraper devuelve una lista vacía, la BD no se ve afectada.
    """
    # === ARRANGE ===
    mocker_rx_session = mocker.patch(
        "agenda_cultural.backend.services.database_service.rx.session"
    )
    mocker_rx_session.return_value.__enter__.return_value = session

    # Tenemos una película guardada
    session.add(
        Movie(
            title="Existing",
            location="a",
            center="A",
            date=datetime(2026, 1, 1),
            url="u",
        )
    )
    session.commit()

    # === ACT ===
    # Le pasamos una lista vacía
    count = sync_movies_to_db([])

    # === ASSERT ===
    assert count == 0
    # La película existente sigue ahí
    assert len(session.exec(select(Movie)).all()) == 1
