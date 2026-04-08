from __future__ import annotations

from dataclasses import dataclass
import logging

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.core.security import get_password_hash
from app.core import database
from app.main import app


logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("passlib").setLevel(logging.ERROR)


@dataclass(frozen=True)
class SeedAccount:
    email: str
    password: str
    nickname: str
    is_superuser: bool = False


ACCOUNTS: list[SeedAccount] = [
    SeedAccount(email="test1@ymd-test.com", password="Test1234!", nickname="测试用户1"),
    SeedAccount(email="test2@ymd-test.com", password="Test1234!", nickname="测试用户2"),
    SeedAccount(email="test3@ymd-test.com", password="Test1234!", nickname="测试用户3"),
    SeedAccount(email="admin@ymd-test.com", password="Admin1234!", nickname="测试管理员", is_superuser=True),
]


def to_sync_db_url(async_url: str) -> str:
    return async_url.replace("postgresql+asyncpg", "postgresql+psycopg2")


def get_user_id_by_email(conn, email: str) -> int | None:
    row = conn.execute(text("select id from users where email = :email"), {"email": email}).fetchone()
    return int(row[0]) if row else None


def upsert_user_login_fields(conn, user_id: int, password: str, nickname: str, is_superuser: bool) -> None:
    conn.execute(
        text(
            """
            update users
            set
              hashed_password = :hashed_password,
              nickname = :nickname,
              is_active = true,
              is_superuser = :is_superuser
            where id = :id
            """
        ),
        {
            "id": user_id,
            "hashed_password": get_password_hash(password),
            "nickname": nickname,
            "is_superuser": bool(is_superuser),
        },
    )


def main() -> None:
    database.engine.echo = False

    sync_url = to_sync_db_url(settings.SQLALCHEMY_DATABASE_URI)
    engine = create_engine(sync_url)

    results: list[dict[str, object]] = []

    with TestClient(app) as client:
        for acc in ACCOUNTS:
            email = acc.email.strip().lower()
            reg = client.post("/api/v1/auth/register", json={"email": email, "password": acc.password})
            created = reg.status_code == 200
            if not created and reg.status_code not in (400, 409):
                raise RuntimeError(f"register failed: {email} status={reg.status_code} body={reg.text}")

            if created:
                user_id = int(reg.json()["user_id"])
            else:
                with engine.begin() as conn:
                    user_id = get_user_id_by_email(conn, email)
                if not user_id:
                    raise RuntimeError(f"user exists but cannot be found in db by email: {email}")

            with engine.begin() as conn:
                upsert_user_login_fields(
                    conn=conn,
                    user_id=user_id,
                    password=acc.password,
                    nickname=acc.nickname,
                    is_superuser=acc.is_superuser,
                )

            results.append(
                {
                    "email": email,
                    "password": acc.password,
                    "user_id": user_id,
                    "role": "admin" if acc.is_superuser else "user",
                    "action": "created" if created else "updated",
                }
            )

    for r in results:
        print(r)


if __name__ == "__main__":
    main()
