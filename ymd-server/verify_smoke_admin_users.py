from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from app.main import app


ADMIN_EMAIL = "admin@ymd-test.com"
ADMIN_PASSWORD = "Admin1234!"

TEST1_EMAIL = "test1@ymd-test.com"
TEST1_PASSWORD = "Test1234!"


def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]


def _login(client: TestClient, *, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, (
        f"login failed for {email}: status={resp.status_code}, body={resp.text}. "
        "如为账号不存在/密码不匹配，请先运行 seed_test_accounts.py"
    )
    data = resp.json()
    assert "access_token" in data, f"login response missing access_token for {email}: {data}"
    return data["access_token"]


if __name__ == "__main__":
    with TestClient(app) as client:
        admin_token = _login(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        admin_headers = {"Authorization": "Bearer " + admin_token}
        r_admin = client.get("/api/v1/admin/users", headers=admin_headers, params={"limit": 1, "offset": 0})
        assert r_admin.status_code == 200, f"admin should be 200, got {r_admin.status_code}: {r_admin.text}"
        assert isinstance(r_admin.json(), list), f"admin /users should return list, got: {type(r_admin.json())}"

        test1_token = _login(client, email=TEST1_EMAIL, password=TEST1_PASSWORD)
        test1_headers = {"Authorization": "Bearer " + test1_token}
        r_user = client.get("/api/v1/admin/users", headers=test1_headers, params={"limit": 1, "offset": 0})
        assert r_user.status_code == 403, f"normal user should be 403, got {r_user.status_code}: {r_user.text}"

        print("smoke_ok", "admin=200", "test1=403")
        print("admin_token_fp", _token_fingerprint(admin_token))
        print("test1_token_fp", _token_fingerprint(test1_token))
