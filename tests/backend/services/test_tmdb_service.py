"""
Pruebas unitarias para el servicio de integración con The Movie Database (TMDB).
Se utiliza 'respx' para interceptar llamadas HTTP, 'pytest-mock' para emular
variables de configuración y 'caplog' para asegurar que el log recibe
el texto esperado.
"""

import pytest
from httpx import ConnectError, Response

from agenda_cultural.backend.config import TMDB_IMAGE_BASE_URL
from agenda_cultural.backend.services.tmdb_service import get_movie_poster


def test_get_movie_poster_no_token(mocker):
    """
    Verifica que la función retorne None de inmediato si no hay un token configurado.
    Este es el caso de 'Fail Fast' para evitar llamadas innecesarias.
    """
    # Arrange: Parcheamos el token en el servicio para que sea None
    mocker.patch("agenda_cultural.backend.services.tmdb_service.TMDB_TOKEN", None)

    # Act: Ejecutamos la función
    result = get_movie_poster("El Exorcista")

    # Assert: Confirmamos que no se intentó ninguna operación
    assert result is None


@pytest.mark.respx(base_url="https://api.themoviedb.org/3")
class TestTMDBApi:
    """
    Grupo de pruebas que requieren la interceptación de llamadas a la API de TMDB.
    Todas las rutas en esta clase son relativas a la base_url definida.
    """

    movie = "Wall-E"

    def test_get_movie_poster_network_failure(self, respx_mock, caplog):
        """Prueba que un fallo crítico de red (DNS/Conexión) sea manejado sin crashear."""
        # Arrange: Simulamos una excepción de conexión de httpx
        respx_mock.get("/search/movie").mock(side_effect=ConnectError)

        # Act
        result = get_movie_poster(self.movie)

        # Assert
        assert result is None
        assert "Error de conexión (Red/DNS) con TMDB" in caplog.text
        assert any(record.levelname == "ERROR" for record in caplog.records)

    @pytest.mark.parametrize("status_code", [400, 401, 404, 500])
    def test_get_movie_poster_http_errors(self, respx_mock, status_code, caplog):
        """
        Verifica que diversos errores de estado HTTP (4xx, 5xx)
        sean capturados por raise_for_status().
        """
        # Arrange: Configuramos el mock con el código de error correspondiente
        respx_mock.get("/search/movie").mock(return_value=Response(status_code))

        # Act
        result = get_movie_poster(self.movie)

        # Assert
        assert result is None
        assert f"Error HTTP {status_code} de TMDB para '{self.movie}'" in caplog.text
        assert any(record.levelname == "ERROR" for record in caplog.records)

    def test_get_movie_poster_no_results(self, respx_mock, caplog):
        """Prueba el comportamiento cuando la API responde OK pero no encuentra la película."""
        # Arrange: TMDB devuelve una lista vacía en 'results'
        mock_response = {"page": 1, "results": [], "total_pages": 1, "total_results": 0}
        respx_mock.get("/search/movie").mock(
            return_value=Response(200, json=mock_response)
        )

        # Act
        result = get_movie_poster(self.movie)

        # Assert
        assert result is None
        assert f"No se encontró póster para '{self.movie}'" in caplog.text
        assert any(record.levelname == "WARNING" for record in caplog.records)

    def test_get_movie_poster_no_poster_path(self, respx_mock, caplog):
        """Prueba el caso donde existe la película pero no tiene imagen cargada (null)."""
        # Arrange: 'poster_path' viene como null (None en Python)
        mock_response = {
            "page": 1,
            "results": [{"poster_path": None}],
            "total_pages": 1,
            "total_results": 1,
        }
        respx_mock.get("/search/movie").mock(
            return_value=Response(200, json=mock_response)
        )

        # Act
        result = get_movie_poster(self.movie)

        # Assert
        assert result is None
        assert f"No se encontró póster para '{self.movie}'" in caplog.text
        assert any(record.levelname == "WARNING" for record in caplog.records)

    def test_get_movie_poster_success(self, respx_mock):
        """
        Caso de éxito: Verifica que se construya correctamente la URL absoluta
        del póster combinando la base de imágenes con el path de la API.
        """
        # Arrange: Simulamos una respuesta exitosa con un path de imagen
        mock_url = "/url_test.jpg"
        mock_response = {
            "page": 1,
            "results": [{"poster_path": mock_url}],
            "total_pages": 1,
            "total_results": 1,
        }
        respx_mock.get("/search/movie").mock(
            return_value=Response(200, json=mock_response)
        )

        # Act
        result = get_movie_poster(self.movie)

        # Assert: Verificamos la construcción correcta del string final
        assert result == f"{TMDB_IMAGE_BASE_URL}{mock_url}"
