import os
import sys
import asyncio
import unittest
from datetime import datetime, timezone

from fastapi import HTTPException

_SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SERVER_ROOT not in sys.path:
    sys.path.insert(0, _SERVER_ROOT)

from app.api.events import list_events
from app.api.posts import list_posts
from app.models.post import Post
from app.models.user import User


class _FakeScalarResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)


class _FakeResult:
    def __init__(self, *, scalars_items=None, rows=None):
        self._scalars_items = scalars_items or []
        self._rows = rows or []

    def scalars(self):
        return _FakeScalarResult(self._scalars_items)

    def all(self):
        return list(self._rows)


class _FakeAsyncSession:
    def __init__(self, *, result: _FakeResult | None = None):
        self.statements = []
        self._result = result or _FakeResult()

    async def execute(self, stmt):
        self.statements.append(stmt)
        return self._result


class LocationRecommendationsRegressionTests(unittest.TestCase):
    def test_user_preferred_location_property_none_when_missing(self):
        u = User()
        self.assertIsNone(u.preferred_location)

    def test_post_model_has_location_columns(self):
        self.assertTrue(hasattr(Post, "lat"))
        self.assertTrue(hasattr(Post, "lng"))
        self.assertTrue(hasattr(Post, "city"))

    def test_events_existing_filters_still_applied(self):
        db = _FakeAsyncSession()
        start_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
        start_to = datetime(2026, 2, 1, tzinfo=timezone.utc)

        asyncio.run(
            list_events(
                limit=50,
                offset=0,
                category="tech",
                city="beijing",
                start_from=start_from,
                start_to=start_to,
                near_lat=None,
                near_lng=None,
                radius_km=None,
                sort="default",
                db=db,
            )
        )

        self.assertEqual(len(db.statements), 1)
        stmt = db.statements[0]
        criteria_text = " ".join(str(c) for c in getattr(stmt, "_where_criteria", ()))
        self.assertIn("events.category", criteria_text)
        self.assertIn("events.city", criteria_text)
        self.assertIn("events.start_at", criteria_text)

    def test_events_near_params_validation(self):
        db = _FakeAsyncSession()
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                list_events(
                    limit=50,
                    offset=0,
                    category=None,
                    city=None,
                    start_from=None,
                    start_to=None,
                    near_lat=39.9,
                    near_lng=None,
                    radius_km=None,
                    sort="default",
                    db=db,
                )
            )
        self.assertEqual(ctx.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx2:
            asyncio.run(
                list_events(
                    limit=50,
                    offset=0,
                    category=None,
                    city=None,
                    start_from=None,
                    start_to=None,
                    near_lat=None,
                    near_lng=None,
                    radius_km=5.0,
                    sort="default",
                    db=db,
                )
            )
        self.assertEqual(ctx2.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx3:
            asyncio.run(
                list_events(
                    limit=50,
                    offset=0,
                    category=None,
                    city=None,
                    start_from=None,
                    start_to=None,
                    near_lat=None,
                    near_lng=None,
                    radius_km=None,
                    sort="distance",
                    db=db,
                )
            )
        self.assertEqual(ctx3.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx4:
            asyncio.run(
                list_events(
                    limit=50,
                    offset=0,
                    category=None,
                    city=None,
                    start_from=None,
                    start_to=None,
                    near_lat=91.0,
                    near_lng=0.0,
                    radius_km=None,
                    sort="default",
                    db=db,
                )
            )
        self.assertEqual(ctx4.exception.status_code, 400)

    def test_posts_near_params_validation(self):
        db = _FakeAsyncSession(result=_FakeResult(rows=[]))

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                list_posts(
                    limit=20,
                    offset=0,
                    user_id=None,
                    near_lat=0.0,
                    near_lng=None,
                    radius_km=None,
                    sort="default",
                    current_user=None,
                    db=db,
                )
            )
        self.assertEqual(ctx.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx2:
            asyncio.run(
                list_posts(
                    limit=20,
                    offset=0,
                    user_id=None,
                    near_lat=None,
                    near_lng=None,
                    radius_km=10.0,
                    sort="default",
                    current_user=None,
                    db=db,
                )
            )
        self.assertEqual(ctx2.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx3:
            asyncio.run(
                list_posts(
                    limit=20,
                    offset=0,
                    user_id=None,
                    near_lat=None,
                    near_lng=None,
                    radius_km=None,
                    sort="distance",
                    current_user=None,
                    db=db,
                )
            )
        self.assertEqual(ctx3.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx4:
            asyncio.run(
                list_posts(
                    limit=20,
                    offset=0,
                    user_id=None,
                    near_lat=-91.0,
                    near_lng=0.0,
                    radius_km=None,
                    sort="default",
                    current_user=None,
                    db=db,
                )
            )
        self.assertEqual(ctx4.exception.status_code, 400)

    def test_posts_default_list_unchanged_no_near_params(self):
        db = _FakeAsyncSession(result=_FakeResult(rows=[]))
        resp = asyncio.run(
            list_posts(
                limit=20,
                offset=0,
                user_id=None,
                near_lat=None,
                near_lng=None,
                radius_km=None,
                sort="default",
                current_user=None,
                db=db,
            )
        )
        self.assertEqual(resp, [])


if __name__ == "__main__":
    unittest.main()
