"""Bearer JWT para admin cross-origin (Pages → Render)."""

from uuid import uuid4

import bcrypt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ...infrastructure.persistence.models import UserModel


def _add_admin(db: Session, *, email: str, username: str) -> str:
    password = "Test1!pass"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
    db.add(
        UserModel(
            id=str(uuid4()),
            email=email,
            username=username,
            hashed_password=hashed,
            is_active=True,
            is_admin=True,
        )
    )
    db.commit()
    return password


class TestBearerAdminAuth:
    def test_login_token_in_body_then_admin_stats_with_bearer(
        self, client: TestClient, db: Session
    ):
        password = _add_admin(
            db, email="bearer-admin@example.com", username="beareradmin"
        )
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "bearer-admin@example.com",
                "password": password,
                "token_in_body": True,
            },
        )
        assert login.status_code == 200
        body = login.json()
        assert body["authenticated"] is True
        assert body["user"]["is_admin"] is True
        assert body.get("access_token")
        assert body.get("refresh_token")
        assert body.get("token_type") == "bearer"
        assert isinstance(body.get("expires_in"), int)

        client.cookies.clear()
        stats = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {body['access_token']}"},
        )
        assert stats.status_code == 200
        data = stats.json()
        for key in (
            "projects",
            "writeups_published",
            "writeups_draft",
            "ctfs",
            "contact_pending",
            "contact_total",
        ):
            assert key in data

    def test_login_default_still_cookie_only_body(self, client: TestClient, db: Session):
        password = _add_admin(
            db, email="cookie-admin@example.com", username="cookieadmin"
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "cookie-admin@example.com", "password": password},
        )
        assert login.status_code == 200
        data = login.json()
        assert data.get("access_token") is None
        assert "access_token" in login.cookies

    def test_bearer_skips_csrf_on_mutating_admin_route(
        self, client: TestClient, db: Session
    ):
        password = _add_admin(
            db, email="csrf-bearer@example.com", username="csrfbearer"
        )
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "csrf-bearer@example.com",
                "password": password,
                "token_in_body": True,
            },
        )
        token = login.json()["access_token"]
        client.cookies.clear()
        res = client.put(
            "/api/v1/portfolio/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Elvis",
                "title": "Dev",
                "bio": "x",
                "avatar_url": None,
                "roles": ["Dev"],
                "stack_items": ["Python"],
                "about_points": ["a"],
                "highlights": [],
                "social_links": {},
            },
        )
        assert res.status_code == 200

    def test_refresh_with_body_token_in_body(self, client: TestClient, db: Session):
        password = _add_admin(
            db, email="refresh-bearer@example.com", username="refreshbearer"
        )
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh-bearer@example.com",
                "password": password,
                "token_in_body": True,
            },
        )
        refresh = login.json()["refresh_token"]
        client.cookies.clear()
        res = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh, "token_in_body": True},
        )
        assert res.status_code == 200
        body = res.json()
        assert body.get("access_token")
        assert body.get("refresh_token")

    def test_empty_bearer_does_not_bypass_csrf_or_use_cookie(
        self, client: TestClient, db: Session
    ):
        """Authorization: Bearer  (vacío) no debe anular CSRF ni usar cookie."""
        password = _add_admin(
            db, email="empty-bearer@example.com", username="emptybearer"
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "empty-bearer@example.com", "password": password},
        )
        assert login.status_code == 200
        assert login.cookies.get("access_token")
        assert login.cookies.get("csrf_token")
        res = client.put(
            "/api/v1/portfolio/profile",
            headers={"Authorization": "Bearer "},
            json={
                "name": "Elvis",
                "title": "Dev",
                "bio": "x",
                "avatar_url": None,
                "roles": ["Dev"],
                "stack_items": ["Python"],
                "about_points": ["a"],
                "highlights": [],
                "social_links": {},
            },
        )
        assert res.status_code in (401, 403)
        assert res.status_code != 200
