"""
Tests de seguridad de writeups y APIs de administración.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ...infrastructure.persistence.models.writeup_model import WriteupModel
from ...infrastructure.persistence.models.ctf_model import CTFModel


CONTENT = "# Writeup\n\n" + ("lorem ipsum " * 20)


def _insert_writeup(
    db: Session,
    *,
    title: str,
    status: str,
    ctf_id: Optional[str] = None,
) -> str:
    wid = str(uuid4())
    db.add(
        WriteupModel(
            id=wid,
            title=title,
            ctf_id=ctf_id,
            content=CONTENT,
            summary="summary",
            tools_used=json.dumps([]),
            techniques=json.dumps([]),
            attachments=json.dumps([]),
            status=status,
            views=0,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    return wid


def _insert_ctf(db: Session) -> str:
    cid = str(uuid4())
    db.add(
        CTFModel(
            id=cid,
            title="Test CTF",
            level="easy",
            category="web",
            platform="HackTheBox",
            status="published",
        )
    )
    db.commit()
    return cid


class TestWriteupDraftLeak:
    """Drafts no deben filtrarse a anónimos ni a usuarios no admin."""

    def test_get_draft_by_id_anonymous_404(self, client: TestClient, db: Session):
        wid = _insert_writeup(db, title="Secret draft", status="draft")
        response = client.get(f"/api/v1/writeups/{wid}")
        assert response.status_code == 404

    def test_get_draft_by_id_non_admin_404(
        self, client: TestClient, db: Session, user_headers: dict
    ):
        wid = _insert_writeup(db, title="Secret draft", status="draft")
        response = client.get(f"/api/v1/writeups/{wid}", headers=user_headers)
        assert response.status_code == 404

    def test_get_draft_by_id_admin_200(
        self, client: TestClient, db: Session, admin_headers: dict
    ):
        wid = _insert_writeup(db, title="Secret draft", status="draft")
        response = client.get(f"/api/v1/writeups/{wid}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Secret draft"
        assert response.json()["status"] == "draft"

    def test_get_published_by_id_anonymous_200(self, client: TestClient, db: Session):
        wid = _insert_writeup(db, title="Public writeup", status="published")
        response = client.get(f"/api/v1/writeups/{wid}")
        assert response.status_code == 200
        assert response.json()["title"] == "Public writeup"

    def test_get_draft_by_ctf_anonymous_404(self, client: TestClient, db: Session):
        ctf_id = _insert_ctf(db)
        _insert_writeup(db, title="CTF draft", status="draft", ctf_id=ctf_id)
        response = client.get(f"/api/v1/writeups/ctf/{ctf_id}")
        assert response.status_code == 404

    def test_get_draft_by_ctf_admin_200(
        self, client: TestClient, db: Session, admin_headers: dict
    ):
        ctf_id = _insert_ctf(db)
        _insert_writeup(db, title="CTF draft", status="draft", ctf_id=ctf_id)
        response = client.get(
            f"/api/v1/writeups/ctf/{ctf_id}", headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "CTF draft"


class TestWriteupAdminList:
    """GET /writeups/admin/all incluye drafts y requiere admin."""

    def test_admin_all_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/writeups/admin/all")
        assert response.status_code in (401, 403)

    def test_admin_all_rejects_non_admin(
        self, client: TestClient, user_headers: dict
    ):
        response = client.get("/api/v1/writeups/admin/all", headers=user_headers)
        assert response.status_code == 403

    def test_admin_all_includes_drafts(
        self, client: TestClient, db: Session, admin_headers: dict
    ):
        _insert_writeup(db, title="Draft one", status="draft")
        _insert_writeup(db, title="Published one", status="published")
        response = client.get("/api/v1/writeups/admin/all", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        titles = {item["title"] for item in data["items"]}
        assert "Draft one" in titles
        assert "Published one" in titles
        assert data["total"] == 2


class TestAdminStats:
    """GET /api/v1/admin/stats."""

    def test_stats_requires_admin(self, client: TestClient):
        response = client.get("/api/v1/admin/stats")
        assert response.status_code in (401, 403)

    def test_stats_counts(
        self, client: TestClient, db: Session, admin_headers: dict
    ):
        _insert_writeup(db, title="Draft one", status="draft")
        _insert_writeup(db, title="Published one", status="published")
        _insert_ctf(db)
        response = client.get("/api/v1/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["projects"] == 0
        assert data["writeups_published"] == 1
        assert data["writeups_draft"] == 1
        assert data["ctfs"] == 1
        assert data["contact_pending"] == 0
        assert data["contact_total"] == 0


class TestRenderMarkdownAuth:
    """POST /writeups/render-markdown requiere admin."""

    def test_render_markdown_anonymous_unauthorized(self, client: TestClient):
        response = client.post(
            "/api/v1/writeups/render-markdown",
            json={"content": "# hi"},
        )
        assert response.status_code in (401, 403)

    def test_render_markdown_admin_ok(
        self, client: TestClient, admin_headers: dict
    ):
        response = client.post(
            "/api/v1/writeups/render-markdown",
            json={"content": "# hi"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "html" in data
        assert "toc" in data
