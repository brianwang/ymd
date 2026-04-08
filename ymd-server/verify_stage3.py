from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4

with TestClient(app) as client:
    inviter_code = "inviter_" + uuid4().hex[:12]
    invitee_code = "invitee_" + uuid4().hex[:12]
    inviter = client.post("/api/v1/auth/wx-login", json={"code": inviter_code}).json()
    invitee = client.post(
        "/api/v1/auth/wx-login",
        json={"code": invitee_code, "inviter_id": inviter["user_id"]},
    ).json()

    headers = {"Authorization": "Bearer " + invitee["access_token"]}

    sign1 = client.post("/api/v1/points/sign-in", headers=headers).json()
    sign2 = client.post("/api/v1/points/sign-in", headers=headers).json()
    ledger = client.get("/api/v1/points/ledger", headers=headers, params={"limit": 10}).json()
    qrcode = client.get("/api/v1/users/invite/qrcode", headers=headers).json()

    print("inviter", inviter)
    print("invitee", invitee)
    print("sign1", sign1)
    print("sign2", sign2)
    print("ledger_len", len(ledger))
    print("qrcode_keys", list(qrcode.keys()))

    assert "access_token" in inviter and "user_id" in inviter
    assert "access_token" in invitee and "user_id" in invitee
    assert sign1["awarded"] in [True, False]
    assert sign2["awarded"] in [True, False]
    assert isinstance(ledger, list)
    assert "png_base64" in qrcode
