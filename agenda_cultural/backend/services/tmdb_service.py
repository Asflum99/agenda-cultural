"""
Servicio de integración con la API de The Movie Database (TMDB).

Permite obtener el póster de la películas mediante búsqueda por el título.
Maneja la autenticación y los posibles errores de red.
"""

import httpx

from agenda_cultural.backend.log_config import get_task_logger
from agenda_cultural.backend.config import (
    TMDB_TOKEN,
    TMDB_BASE_URL,
    TMDB_IMAGE_BASE_URL,
)

# Usamos 'scraping.log' para centralizar todo el flujo del proceso en un solo lugar.
logger = get_task_logger("tmdb_service", "scraping.log")

# Validación de Configuración (Se ejecuta una sola vez al cargar el módulo)
if not TMDB_TOKEN:
    logger.error(
        "TMDB_TOKEN no configurado. El servicio de imágenes estará deshabilitado."
    )


def get_movie_poster(title: str) -> str | None:
    """
    Busca una película por su título en TMDB y devuelve la URL absoluta de su póster.

    Args:
        title (str): Título de la película a buscar.

    Returns:
        str | None: URL de la imagen si se encuentra, o None si falla/no existe.
    """
    # Chequeo rápido (Fail Fast): Si no hay token, salimos silenciosamente
    # porque ya avisamos en el log al inicio del archivo.
    if not TMDB_TOKEN:
        return None

    headers = {"accept": "application/json", "Authorization": f"Bearer {TMDB_TOKEN}"}

    params = {
        "query": title,
        "include_adult": "false",
        "language": "es-PE",
        "page": 1,
    }

    url = f"{TMDB_BASE_URL}/search/movie"

    try:
        # Usamos el cliente como Context Manager para asegurar que se cierre la conexión
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params, timeout=10.0)

            # Si hay error (401, 404, 500), lanzamos excepción para capturarla abajo
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if results:
                # Tomamos el primer resultado como la mejor coincidencia
                best_match = results[0]
                poster_path = best_match.get("poster_path")

                if poster_path:
                    return f"{TMDB_IMAGE_BASE_URL}{poster_path}"

            # Si llegamos aquí, la búsqueda fue exitosa pero no trajo resultados o imagen
            logger.warning(f"No se encontró póster para '{title}'")
            return None

    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP {e.response.status_code} de TMDB para '{title}'")
        return None
    except httpx.RequestError as e:
        logger.error(f"Error de conexión (Red/DNS) con TMDB: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado procesando '{title}': {e}", exc_info=True)
        return None
