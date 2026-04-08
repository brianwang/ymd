from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.main import app


with TestClient(app) as client:
    space_id = 123
    phone = "13800138000"

    anon_created = client.post(
        f"/api/v1/coliving/spaces/{space_id}/inquiries",
        json={"contact_phone": phone, "message": "anon " + uuid4().hex[:8]},
    )
    assert anon_created.status_code == 201
    anon_id = anon_created.json()["id"]

    wx = client.post("/api/v1/auth/wx-login", json={"code": "inq_" + uuid4().hex[:12]}).json()
    user_headers = {"Authorization": "Bearer " + wx["access_token"]}
    authed_created = client.post(
        f"/api/v1/coliving/spaces/{space_id}/inquiries",
        headers=user_headers,
        json={"contact_phone": phone, "message": "authed " + uuid4().hex[:8]},
    )
    assert authed_created.status_code == 201
    inquiry_id = authed_created.json()["id"]

    admin_email = f"admin_{uuid4().hex[:10]}@example.com"
    admin_pwd = "ap_" + uuid4().hex[:12]
    admin_reg = client.post("/api/v1/auth/register", json={"email": admin_email, "password": admin_pwd}).json()
    sync_url = settings.SQLALCHEMY_DATABASE_URI.replace("postgresql+asyncpg", "postgresql+psycopg2")
    engine = create_engine(sync_url)
    with engine.begin() as conn:
        conn.execute(text("update users set is_superuser = true where id = :id"), {"id": admin_reg["user_id"]})
    admin_login = client.post("/api/v1/auth/login", json={"email": admin_email, "password": admin_pwd}).json()
    admin_headers = {"Authorization": "Bearer " + admin_login["access_token"]}

    listed = client.get(
        "/api/v1/admin/coliving/inquiries",
        headers=admin_headers,
        params={"limit": 20, "offset": 0, "keyword": phone},
    )
    assert listed.status_code == 200
    data = listed.json()
    assert data["total"] >= 1
    assert any(x["id"] == inquiry_id for x in data["items"])

    patched = client.patch(
        f"/api/v1/admin/coliving/inquiries/{inquiry_id}",
        headers=admin_headers,
        json={"status": "contacted", "admin_note": "ok " + uuid4().hex[:6]},
    )
    assert patched.status_code == 200
    patched_data = patched.json()
    assert patched_data["status"] == "contacted"

    print("anon_inquiry_id", anon_id)
    print("authed_inquiry_id", inquiry_id)
    print("admin_user_id", admin_reg["user_id"])
