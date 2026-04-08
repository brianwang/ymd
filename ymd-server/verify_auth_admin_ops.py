from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from app.main import app
from app.core.config import settings

with TestClient(app) as client:
    email = f"u_{uuid4().hex[:10]}@example.com"
    password = "p_" + uuid4().hex[:12]

    reg = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    reg_data = reg.json()
    assert "access_token" in reg_data and "user_id" in reg_data

    reg2 = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg2.status_code in [400, 409]

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    login_data = login.json()
    assert "access_token" in login_data and "user_id" in login_data

    wx = client.post("/api/v1/auth/wx-login", json={"code": "bind_" + uuid4().hex[:10]}).json()
    wx_headers = {"Authorization": "Bearer " + wx["access_token"]}
    bind_email = f"b_{uuid4().hex[:10]}@example.com"
    bind_pwd = "bp_" + uuid4().hex[:12]
    bind = client.post("/api/v1/users/bind-email", headers=wx_headers, json={"email": bind_email, "password": bind_pwd})
    assert bind.status_code == 200
    me = client.get("/api/v1/users/me", headers=wx_headers).json()
    assert me["email"] == bind_email

    login2 = client.post("/api/v1/auth/login", json={"email": bind_email, "password": bind_pwd})
    assert login2.status_code == 200

    non_admin = client.get("/api/v1/admin/users", headers=wx_headers)
    assert non_admin.status_code == 403

    admin_reg_email = f"admin_{uuid4().hex[:10]}@example.com"
    admin_reg_pwd = "ap_" + uuid4().hex[:12]
    admin_reg = client.post("/api/v1/auth/register", json={"email": admin_reg_email, "password": admin_reg_pwd}).json()
    sync_url = settings.SQLALCHEMY_DATABASE_URI.replace("postgresql+asyncpg", "postgresql+psycopg2")
    engine = create_engine(sync_url)
    with engine.begin() as conn:
        conn.execute(text("update users set is_superuser = true where id = :id"), {"id": admin_reg["user_id"]})
    admin_login = client.post("/api/v1/auth/login", json={"email": admin_reg_email, "password": admin_reg_pwd}).json()
    admin_headers = {"Authorization": "Bearer " + admin_login["access_token"]}

    users = client.get("/api/v1/admin/users", headers=admin_headers, params={"limit": 10, "offset": 0})
    assert users.status_code == 200
    assert isinstance(users.json(), list)

    defaults = {
        "sign_in_points": settings.SIGN_IN_POINTS,
        "inviter_reward_points": settings.INVITER_REWARD_POINTS,
        "invitee_reward_points": settings.INVITEE_REWARD_POINTS,
        "first_post_points": settings.FIRST_POST_POINTS,
        "post_reward_points": settings.POST_REWARD_POINTS,
        "comment_reward_points": settings.COMMENT_REWARD_POINTS,
        "daily_post_reward_limit": settings.DAILY_POST_REWARD_LIMIT,
        "daily_comment_reward_limit": settings.DAILY_COMMENT_REWARD_LIMIT,
    }

    updated = client.put("/api/v1/admin/reward-config", headers=admin_headers, json={"sign_in_points": 123})
    assert updated.status_code == 200
    cfg = client.get("/api/v1/admin/reward-config", headers=admin_headers).json()
    assert cfg["sign_in_points"] == 123

    u2 = client.post("/api/v1/auth/wx-login", json={"code": "sign_" + uuid4().hex[:10]}).json()
    u2_headers = {"Authorization": "Bearer " + u2["access_token"]}
    sign = client.post("/api/v1/points/sign-in", headers=u2_headers).json()
    assert sign["delta"] == 123

    restored = client.put("/api/v1/admin/reward-config", headers=admin_headers, json=defaults)
    assert restored.status_code == 200

    print("register_user_id", reg_data["user_id"])
    print("bind_user_id", wx["user_id"])
    print("admin_user_id", admin_reg["user_id"])
