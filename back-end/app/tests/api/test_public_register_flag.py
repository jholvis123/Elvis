"""Tests for ALLOW_PUBLIC_REGISTER gate on POST /auth/register."""

from fastapi.testclient import TestClient

from ...core.config import settings


class TestPublicRegisterFlag:
    def test_register_rejected_when_flag_off(self, client: TestClient):
        # client fixture enables register; turn it off for this case
        settings.ALLOW_PUBLIC_REGISTER = False
        try:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "blocked@example.com",
                    "username": "blockeduser",
                    "password": "Test1!pass",
                },
            )
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower()
        finally:
            settings.ALLOW_PUBLIC_REGISTER = True

    def test_register_allowed_when_flag_on(self, client: TestClient):
        settings.ALLOW_PUBLIC_REGISTER = True
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "allowed@example.com",
                "username": "alloweduser",
                "password": "Test1!pass",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "allowed@example.com"
        assert body["username"] == "alloweduser"
