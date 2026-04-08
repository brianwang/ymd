from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app


with TestClient(app) as client:
    code = "user_" + uuid4().hex[:12]
    user = client.post("/api/v1/auth/wx-login", json={"code": code}).json()
    headers = {"Authorization": "Bearer " + user["access_token"]}

    created = client.post(
        "/api/v1/posts",
        headers=headers,
        json={"content": "hello " + uuid4().hex[:8], "image_urls": []},
    ).json()
    post_id = created["id"]

    listed = client.get("/api/v1/posts", headers=headers, params={"limit": 10, "offset": 0}).json()
    assert any(p["id"] == post_id for p in listed)

    detail1 = client.get(f"/api/v1/posts/{post_id}", headers=headers).json()
    assert detail1["id"] == post_id

    like1 = client.post(f"/api/v1/posts/{post_id}/like", headers=headers).json()
    assert like1["liked"] is True

    like2 = client.post(f"/api/v1/posts/{post_id}/like", headers=headers).json()
    assert like2["liked"] is False

    comment = client.post(
        f"/api/v1/posts/{post_id}/comments",
        headers=headers,
        json={"content": "c " + uuid4().hex[:8]},
    ).json()
    comment_id = comment["id"]

    comments = client.get(
        f"/api/v1/posts/{post_id}/comments",
        headers=headers,
        params={"limit": 50, "offset": 0},
    ).json()
    assert any(c["id"] == comment_id for c in comments)

    detail2 = client.get(f"/api/v1/posts/{post_id}", headers=headers).json()
    assert detail2["comment_count"] >= 1

    ledger = client.get("/api/v1/points/ledger", headers=headers, params={"limit": 50, "offset": 0}).json()
    assert any(x["event_type"] == "post_reward" and str(post_id) in x["biz_key"] for x in ledger)
    assert any(x["event_type"] == "comment_reward" and str(comment_id) in x["biz_key"] for x in ledger)

    print("user_id", user["user_id"])
    print("post_id", post_id)
    print("comment_id", comment_id)
    print("ledger_len", len(ledger))
