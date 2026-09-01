"""
Tests del endurecimiento round 3: refresh rotación, perfil persistido,
docs solo en DEBUG, AuthStatus sin tokens en body.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _register_and_login(client: TestClient, email: str = "round3@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": email.split("@")[0][:20],
            "password": "securepassword123",
        },
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword123"},
    )


class TestAuthStatusAndRefreshRotation:
    def test_login_body_is_auth_status_not_tokens(self, client: TestClient):
        response = _register_and_login(client)
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) >= {"authenticated", "user", "expires_in"}
        assert "access_token" not in data
        assert "refresh_token" not in data
        assert "token_type" not in data

    def test_refresh_sets_new_refresh_cookie(self, client: TestClient):
        login = _register_and_login(client, email="refresh@example.com")
        assert login.status_code == 200
        old_refresh = login.cookies.get("refresh_token")
        assert old_refresh

        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert "access_token" not in data
        assert "user" in data
        assert "expires_in" in data
        new_refresh = response.cookies.get("refresh_token")
        assert new_refresh
        assert new_refresh != old_refresh


class TestDocsHiddenWhenNotDebug:
    def test_docs_unavailable_when_debug_false(self, client: TestClient):
        from ...core.config import settings

        if settings.DEBUG:
            return
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404


class TestPortfolioProfilePersistence:
    def test_get_profile_falls_back_to_default(self, client: TestClient):
        response = client.get("/api/v1/portfolio/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Elvis"
        assert "roles" in data
        assert "stack_items" in data
        assert "about_points" in data
        assert "highlights" in data
        assert "social_links" in data

    def test_contact_info_shape(self, client: TestClient):
        response = client.get("/api/v1/portfolio/contact-info")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "github" in data
        assert "linkedin" in data
        assert "twitter" in data

    def test_put_profile_requires_admin(self, client: TestClient, user_headers: dict):
        payload = client.get("/api/v1/portfolio/profile").json()
        payload["name"] = "Hacker"
        anon = client.put("/api/v1/portfolio/profile", json=payload)
        assert anon.status_code in (401, 403)
        user = client.put(
            "/api/v1/portfolio/profile", json=payload, headers=user_headers
        )
        assert user.status_code == 403

    def test_put_profile_persists_and_matches_get_shape(
        self, client: TestClient, admin_headers: dict
    ):
        original = client.get("/api/v1/portfolio/profile").json()
        payload = dict(original)
        payload["name"] = "Elvis Persistido"
        payload["title"] = "Updated Title"
        payload["bio"] = "Bio persistida"
        payload["social_links"] = {
            **original.get("social_links", {}),
            "twitter": "https://twitter.com/elvis",
        }

        put = client.put(
            "/api/v1/portfolio/profile",
            json=payload,
            headers=admin_headers,
        )
        assert put.status_code == 200, put.text
        body = put.json()
        assert body["name"] == "Elvis Persistido"
        assert body["title"] == "Updated Title"
        assert body["bio"] == "Bio persistida"
        assert set(body.keys()) == set(original.keys())

        got = client.get("/api/v1/portfolio/profile")
        assert got.status_code == 200
        assert got.json()["name"] == "Elvis Persistido"
        assert got.json()["title"] == "Updated Title"

        contact = client.get("/api/v1/portfolio/contact-info").json()
        assert contact["twitter"] == "https://twitter.com/elvis"
        assert contact["email"]
