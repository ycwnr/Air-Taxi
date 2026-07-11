"""network/distance_calculator.py — great-circle distance matrix (mirrors the
haversine() implementation used in the Leaflet HTML dashboard, for numeric
consistency with the reference visualization)."""
import math


def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def build_distance_matrix(vertiports: dict) -> dict:
    """vertiports: {id: Vertiport}. Returns dist[a][b] in km, rounded like the dashboard."""
    ids = list(vertiports.keys())
    dist = {a: {} for a in ids}
    for a in ids:
        for b in ids:
            va, vb = vertiports[a], vertiports[b]
            dist[a][b] = round(haversine(va.lat, va.lon, vb.lat, vb.lon), 2)
    return dist
