"""Health alias and CORS defaults for Render + GitHub Pages."""

from fastapi.testclient import TestClient

from ...core.config import Settings, settings


class TestHealthAndCorsRender:
    def test_health_root(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["db"] == "ok"

    def test_health_api_v1_alias(self, client: TestClient):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["db"] == "ok"

    def test_default_cors_includes_pages_origin(self):
        assert "https://jholvis123.github.io" in settings.CORS_ORIGINS

    def test_normalize_render_postgres_url(self):
        assert (
            Settings.normalize_database_url("postgres://u:p@h:5432/db")
            == "postgresql+psycopg2://u:p@h:5432/db"
        )
        assert (
            Settings.normalize_database_url("postgresql://u:p@h:5432/db")
            == "postgresql+psycopg2://u:p@h:5432/db"
        )
        assert (
            Settings.normalize_database_url("postgresql+psycopg2://u:p@h:5432/db")
            == "postgresql+psycopg2://u:p@h:5432/db"
        )
        assert (
            Settings.normalize_database_url("mysql+pymysql://root:@localhost:3306/db")
            == "mysql+pymysql://root:@localhost:3306/db"
        )
