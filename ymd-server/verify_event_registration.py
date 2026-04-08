from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.main import app


def to_sync_db_url(async_url: str) -> str:
    return async_url.replace("postgresql+asyncpg", "postgresql+psycopg2")


with TestClient(app) as client:
    admin_email = f"admin_{uuid4().hex[:10]}@example.com"
    admin_pwd = "Admin_" + uuid4().hex[:12]
    admin_reg = client.post("/api/v1/auth/register", json={"email": admin_email, "password": admin_pwd})
    assert admin_reg.status_code == 200, admin_reg.text
    admin_id = admin_reg.json()["user_id"]

    sync_url = to_sync_db_url(settings.SQLALCHEMY_DATABASE_URI)
    engine = create_engine(sync_url)
    with engine.begin() as conn:
        conn.execute(text("update users set is_superuser = true where id = :id"), {"id": admin_id})

    admin_login = client.post("/api/v1/auth/login", json={"email": admin_email, "password": admin_pwd})
    assert admin_login.status_code == 200, admin_login.text
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": "Bearer " + admin_token}

    user_email = f"u_{uuid4().hex[:10]}@example.com"
    user_pwd = "Pwd_" + uuid4().hex[:12]
    user_reg = client.post("/api/v1/auth/register", json={"email": user_email, "password": user_pwd})
    assert user_reg.status_code == 200, user_reg.text
    user_login = client.post("/api/v1/auth/login", json={"email": user_email, "password": user_pwd})
    assert user_login.status_code == 200, user_login.text
    user_headers = {"Authorization": "Bearer " + user_login.json()["access_token"]}

    user2_email = f"u2_{uuid4().hex[:10]}@example.com"
    user2_pwd = "Pwd2_" + uuid4().hex[:12]
    user2_reg = client.post("/api/v1/auth/register", json={"email": user2_email, "password": user2_pwd})
    assert user2_reg.status_code == 200, user2_reg.text
    user2_login = client.post("/api/v1/auth/login", json={"email": user2_email, "password": user2_pwd})
    assert user2_login.status_code == 200, user2_login.text
    user2_headers = {"Authorization": "Bearer " + user2_login.json()["access_token"]}

    now = datetime.utcnow()
    start_at = now + timedelta(days=2)
    deadline = now + timedelta(days=1)

    created = client.post(
        "/api/v1/admin/events",
        headers=admin_headers,
        json={
            "title": "测试活动_" + uuid4().hex[:6],
            "category": "共创",
            "city": "上海",
            "address": "测试地址",
            "cover_url": None,
            "summary": "summary",
            "content": "content",
            "start_at": start_at.isoformat() + "Z",
            "end_at": None,
            "signup_deadline_at": deadline.isoformat() + "Z",
            "capacity": 1,
        },
    )
    assert created.status_code == 201, created.text
    event = created.json()
    event_id = event["id"]

    pub = client.patch(
        f"/api/v1/admin/events/{event_id}/publish",
        headers=admin_headers,
        json={"is_published": True},
    )
    assert pub.status_code == 200, pub.text

    lst = client.get("/api/v1/events")
    assert lst.status_code == 200, lst.text
    assert any(it["id"] == event_id for it in lst.json())

    detail = client.get(f"/api/v1/events/{event_id}", headers=user_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["my_registration_status"] == "none"

    r1 = client.post(
        f"/api/v1/events/{event_id}/registrations",
        headers=user_headers,
        json={"name": "张三", "phone": "13800000000", "remark": "备注"},
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["status"] == "registered"
    assert r1.json()["registered_count"] == 1

    r1_again = client.post(
        f"/api/v1/events/{event_id}/registrations",
        headers=user_headers,
        json={"name": "张三", "phone": "13800000000", "remark": "备注"},
    )
    assert r1_again.status_code == 200, r1_again.text
    assert r1_again.json()["registered_count"] == 1

    r2 = client.post(
        f"/api/v1/events/{event_id}/registrations",
        headers=user2_headers,
        json={"name": "李四", "phone": "13900000000", "remark": ""},
    )
    assert r2.status_code == 400, r2.text

    c1 = client.post(f"/api/v1/events/{event_id}/registrations/cancel", headers=user_headers)
    assert c1.status_code == 200, c1.text
    assert c1.json()["registered_count"] == 0

    r2_retry = client.post(
        f"/api/v1/events/{event_id}/registrations",
        headers=user2_headers,
        json={"name": "李四", "phone": "13900000000", "remark": ""},
    )
    assert r2_retry.status_code == 200, r2_retry.text
    assert r2_retry.json()["registered_count"] == 1

    me = client.get("/api/v1/events/registrations/me", headers=user2_headers)
    assert me.status_code == 200, me.text
    assert any(it["event"]["id"] == event_id for it in me.json())

    regs = client.get(f"/api/v1/admin/events/{event_id}/registrations", headers=admin_headers)
    assert regs.status_code == 200, regs.text
    assert any(it["user_id"] == user2_reg.json()["user_id"] for it in regs.json())

    print("event_id", event_id)

