from .cultural_centers import CULTURAL_CENTERS


def get_all_center_keys() -> list[str]:
    """Obtiene todas las claves de centros culturales."""
    return list(CULTURAL_CENTERS.keys())


def get_center_info(center_key: str) -> dict[str, str]:
    """Obtiene toda la información del centro cultural."""
    return CULTURAL_CENTERS.get(center_key, {})
