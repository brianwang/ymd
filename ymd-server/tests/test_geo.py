import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

_SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SERVER_ROOT not in sys.path:
    sys.path.insert(0, _SERVER_ROOT)

from app.utils.geo import (
    validate_lat_lng,
    haversine_km,
    round_distance_km,
    stable_distance_sort_key,
)


class GeoTests(unittest.TestCase):
    def test_validate_lat_lng_ok(self):
        validate_lat_lng(lat=0.0, lng=0.0)
        validate_lat_lng(lat=90.0, lng=180.0)
        validate_lat_lng(lat=-90.0, lng=-180.0)

    def test_validate_lat_lng_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_lat_lng(lat=90.0001, lng=0.0)
        with self.assertRaises(ValueError):
            validate_lat_lng(lat=0.0, lng=180.0001)

    def test_haversine_and_rounding(self):
        d = haversine_km(lat1=0.0, lng1=0.0, lat2=0.0, lng2=1.0)
        self.assertTrue(110.0 < d < 112.5)
        self.assertEqual(round_distance_km(d), 111.2)

    def test_radius_filtering(self):
        near_lat, near_lng = 0.0, 0.0
        points = [
            ("near", 0.0, 0.0),
            ("~55km", 0.0, 0.5),
            ("~111km", 0.0, 1.0),
        ]
        within_60 = [name for (name, lat, lng) in points if haversine_km(lat1=near_lat, lng1=near_lng, lat2=lat, lng2=lng) <= 60]
        self.assertEqual(within_60, ["near", "~55km"])

    def test_stable_distance_sort_key(self):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        items = [
            ("no_loc_new", None, base + timedelta(hours=2), 200),
            ("d10_old", 10.0, base, 1),
            ("d10_new", 10.0, base + timedelta(hours=1), 2),
            ("d5_mid", 5.0, base + timedelta(minutes=30), 3),
            ("no_loc_old", None, base, 100),
        ]
        sorted_names = [
            name
            for (name, _, _, _) in sorted(
                items, key=lambda it: stable_distance_sort_key(distance_km=it[1], created_at=it[2], entity_id=it[3])
            )
        ]
        self.assertEqual(sorted_names, ["d5_mid", "d10_new", "d10_old", "no_loc_new", "no_loc_old"])


if __name__ == "__main__":
    unittest.main()
