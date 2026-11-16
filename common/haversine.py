"""Calcul de distance entre deux points GPS (formule de Haversine)."""
import math


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Retourne la distance en kilomètres entre deux coordonnées."""
    r = 6371.0  # rayon moyen de la Terre en km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c
