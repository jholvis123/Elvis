"""
Tests de endurecimiento: filtros 400, 500 genérico, rate limit de contacto
y límite de render-markdown.
"""

from fastapi.testclient import TestClient


UNHANDLED_DETAIL = "No fue posible completar la operación. Intenta nuevamente."

CONTACT_PAYLOAD = {
    "name": "Juan Perez",
    "email": "juan@example.com",
    "project_type": "web",
    "message": "Hola, me gustaria hablar sobre un proyecto web.",
}


class TestInvalidStatusQuery:
    """Query status inválido debe ser 400, no 500."""

    def test_writeups_admin_all_invalid_status_400(
        self, client: TestClient, admin_headers: dict
    ):
        response = client.get(
            "/api/v1/writeups/admin/all",
            params={"status": "not-a-real-status"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        body = response.json()
        assert "detail" in body
        assert "traceback" not in response.text.lower()
        assert "ValueError" not in response.text

    def test_contact_invalid_status_filter_400(
        self, client: TestClient, admin_headers: dict
    ):
        response = client.get(
            "/api/v1/contact",
            params={"status_filter": "not-a-real-status"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "traceback" not in response.text.lower()


class TestUnhandledException:
    """Excepciones no controladas: 500 genérico, sin traceback en el body."""

    def test_unhandled_exception_generic_500_no_traceback(self, client: TestClient):
        from ...main import app

        async def _boom():
            raise RuntimeError("secret internals xyz")

        app.add_api_route(
            "/__test_unhandled_boom",
            _boom,
            methods=["GET"],
            name="__test_unhandled_boom",
        )
        try:
            response = client.get("/__test_unhandled_boom")
            assert response.status_code == 500
            assert response.json() == {"detail": UNHANDLED_DETAIL}
            text = response.text
            assert "secret internals xyz" not in text
            assert "Traceback" not in text
            assert "RuntimeError" not in text
        finally:
            app.router.routes = [
                route
                for route in app.router.routes
                if getattr(route, "path", None) != "/__test_unhandled_boom"
            ]


class TestContactRateLimit:
    """POST /contact usa el limiter compartido: 5/hora por IP."""

    def test_contact_post_limited_to_5_per_hour(self, client: TestClient):
        codes = []
        for i in range(6):
            payload = dict(CONTACT_PAYLOAD)
            payload["email"] = f"juan{i}@example.com"
            response = client.post("/api/v1/contact", json=payload)
            codes.append(response.status_code)
        assert codes[:5] == [201, 201, 201, 201, 201], codes
        assert codes[5] == 429


class TestRenderMarkdownLimit:
    """POST /writeups/render-markdown rechaza contenido > 100000 chars."""

    def test_render_markdown_rejects_content_over_100000(
        self, client: TestClient, admin_headers: dict
    ):
        response = client.post(
            "/api/v1/writeups/render-markdown",
            json={"content": "a" * 100001},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "detail" in response.json()
