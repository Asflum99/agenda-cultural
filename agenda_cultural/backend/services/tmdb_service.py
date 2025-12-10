import httpx

from agenda_cultural.backend.log_config import get_task_logger
from agenda_cultural.backend.config import (
    TMDB_TOKEN,
    TMDB_BASE_URL,
    TMDB_IMAGE_BASE_URL,
)

logger = get_task_logger("tmdb_client", "tmdb_integration.log")


def get_movie_poster(title: str) -> str | None:
    """
    Busca una película por título y devuelve la URL absoluta de su póster.
    """
    if not TMDB_TOKEN:
        logger.critical("⚠️ TMDB_TOKEN no configurado en .env")
        return None

    # Headers de autenticación
    headers = {"accept": "application/json", "Authorization": f"Bearer {TMDB_TOKEN}"}

    # Parámetros de búsqueda
    params = {
        "query": title,
        "include_adult": False,
        "language": "es-PE",
        "page": 1,
    }

    url = f"{TMDB_BASE_URL}/search/movie"

    try:
        with httpx.Client() as client:
            # Hacemos la petición GET con timeout de 10s
            response = client.get(url, headers=headers, params=params, timeout=10.0)

            # Si hay error (401, 404, 500), lanzamos excepción
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if results:
                # 1. Tomamos el primer resultado (el más relevante)
                best_match = results[0]

                # 2. Extraemos el 'poster_path'
                poster_path = best_match.get("poster_path")

                if poster_path:
                    # 3. Construimos la URL final
                    full_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
                    return full_url

            logger.warning(f"❌ No se encontró póster para '{title}'")
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
