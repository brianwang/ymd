from __future__ import annotations

import math
from typing import Any

from sqlalchemy import Float
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql import func as sa_func

EARTH_RADIUS_KM = 6371.0


def validate_lat_lng(*, lat: float, lng: float) -> None:
    if lat < -90 or lat > 90:
        raise ValueError("lat must be between -90 and 90")
    if lng < -180 or lng > 180:
        raise ValueError("lng must be between -180 and 180")


def haversine_km(*, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Great-circle distance between two points on a sphere given their longitudes and latitudes.
    Returns kilometers.
    """
    validate_lat_lng(lat=lat1, lng=lng1)
    validate_lat_lng(lat=lat2, lng=lng2)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return EARTH_RADIUS_KM * c


def round_distance_km(distance_km: float) -> float:
    # 四舍五入到 0.1km
    return round(distance_km + 1e-9, 1)


def sql_distance_km_expr(*, lat_col: Any, lng_col: Any, near_lat: float, near_lng: float) -> ColumnElement[float]:
    """
    SQLAlchemy distance expression (km) for PostgreSQL without PostGIS, using Haversine.
    Note: `lat_col/lng_col` should be model columns (nullable allowed).
    """
    # Guard rails: don't silently accept invalid query inputs
    validate_lat_lng(lat=near_lat, lng=near_lng)

    lat1 = sa_func.radians(near_lat)
    lat2 = sa_func.radians(lat_col)
    d_lat = sa_func.radians(lat_col - near_lat)
    d_lng = sa_func.radians(lng_col - near_lng)

    a = sa_func.pow(sa_func.sin(d_lat / 2.0), 2) + sa_func.cos(lat1) * sa_func.cos(lat2) * sa_func.pow(
        sa_func.sin(d_lng / 2.0), 2
    )
    c = 2.0 * sa_func.asin(sa_func.sqrt(a))
    # Cast helps SQLAlchemy typing and prevents integer math surprises
    return sa_func.cast(EARTH_RADIUS_KM * c, Float)

