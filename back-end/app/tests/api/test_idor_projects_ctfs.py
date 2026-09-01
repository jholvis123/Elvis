"""
IDOR / authz: proyectos y CTFs no publicados no se filtran por ID.
Estadísticas de CTF no deben 500. Submit de flag incluye is_correct y success.
"""

import hashlib
import json
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ...infrastructure.persistence.models.ctf_model import CTFModel
from ...infrastructure.persistence.models.project_model import ProjectModel


def _insert_project(
    db: Session,
    *,
    title: str,
    status: str,
    featured: bool = False,
) -> str:
    pid = str(uuid4())
    db.add(
        ProjectModel(
            id=pid,
            title=title,
            description="secret project description",
            short_description="short",
            technologies=json.dumps(["python"]),
            highlights=json.dumps([]),
            status=status,
            featured=featured,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    return pid


def _insert_ctf(
    db: Session,
    *,
    title: str = "Secret CTF",
    status: str = "draft",
    is_active: bool = True,
    flag: str = "flag{test}",
    description: str = "secret ctf description",
) -> str:
    cid = str(uuid4())
    db.add(
        CTFModel(
            id=cid,
            title=title,
            level="easy",
            category="web",
            platform="HackTheBox",
            description=description,
            points=100,
            hints=json.dumps(["secret hint"]),
            skills=json.dumps(["web"]),
            flag_hash=hashlib.sha256(flag.encode()).hexdigest(),
            is_flag_regex=False,
            status=status,
            is_active=is_active,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    return cid


class TestProjectIdor:
    """GET /projects/{id}: draft 404 anónimo; admin 200; listado público solo published."""

    def test_get_draft_project_anonymous_404(self, client: TestClient, db: Session):
        pid = _insert_project(db, title="Draft project", status="draft")
        response = client.get(f"/api/v1/projects/{pid}")
        assert response.status_code == 404
        body = response.json()
        assert "detail" in body
        text = response.text.lower()
        assert "secret project description" not in text
        assert "draft project" not in text

    def test_get_draft_project_non_admin_404(
        self, client: TestClient, db: Session, user_headers: dict
    ):
        pid = _insert_project(db, title="Draft project", status="draft")
        response = client.get(f"/api/v1/projects/{pid}", headers=user_headers)
        assert response.status_code == 404

    def test_get_draft_project_admin_200(
        self, client: TestClient, db: Session, admin_headers: dict
    ):
        pid = _insert_project(db, title="Draft project", status="draft")
        response = client.get(f"/api/v1/projects/{pid}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Draft project"
        assert data["status"] == "draft"
        assert data["id"] == pid

    def test_get_published_project_anonymous_200(self, client: TestClient, db: Session):
        pid = _insert_project(db, title="Public project", status="published")
        response = client.get(f"/api/v1/projects/{pid}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Public project"
        assert data["status"] == "published"
        assert data["id"] == pid

    def test_public_list_published_only(self, client: TestClient, db: Session):
        _insert_project(db, title="Draft project", status="draft")
        _insert_project(db, title="Public project", status="published")
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        titles = {item["title"] for item in data["items"]}
        assert "Public project" in titles
        assert "Draft project" not in titles
        assert all(item["status"] == "published" for item in data["items"])


class TestCtfIdor:
    """GET /ctfs/{id} y POST submit: unpublished 404 para no-admin."""

    def test_get_draft_ctf_anonymous_404(self, client: TestClient, db: Session):
        cid = _insert_ctf(db, title="Draft CTF", status="draft")
        response = client.get(f"/api/v1/ctfs/{cid}")
        assert response.status_code == 404
        text = response.text.lower()
        assert "secret ctf description" not in text
        assert "secret hint" not in text
        assert "draft ctf" not in text
        assert "flag_hash" not in text
        body = response.json()
        assert "description" not in body
        assert "hints" not in body
        assert "attachments" not in body
        assert "status" not in body

    def test_get_draft_ctf_non_admin_404(
        self, client: TestClient, db: Session, user_headers: dict
    ):
        cid = _insert_ctf(db, title="Draft CTF", status="draft")
        response = client.get(f"/api/v1/ctfs/{cid}", headers=user_headers)
        assert response.status_code == 404

    def test_get_draft_ctf_admin_200(
        self, client: TestClient, db: Session, admin_headers: dict
    ):
        cid = _insert_ctf(db, title="Draft CTF", status="draft")
        response = client.get(f"/api/v1/ctfs/{cid}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Draft CTF"
        assert data["status"] == "draft"
        assert "flag_hash" not in data
        assert "flagHash" not in data

    def test_get_published_ctf_anonymous_200(self, client: TestClient, db: Session):
        cid = _insert_ctf(db, title="Public CTF", status="published")
        response = client.get(f"/api/v1/ctfs/{cid}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Public CTF"
        assert data["status"] == "published"
        assert "flag_hash" not in data

    def test_submit_unpublished_active_anonymous_404(self, client: TestClient, db: Session):
        cid = _insert_ctf(
            db, title="Draft active CTF", status="draft", is_active=True
        )
        response = client.post(
            f"/api/v1/ctfs/{cid}/submit",
            json={"flag": "flag{test}"},
        )
        assert response.status_code == 404
        text = response.text.lower()
        assert "secret ctf description" not in text
        assert "secret hint" not in text

    def test_submit_unpublished_active_non_admin_404(
        self, client: TestClient, db: Session, user_headers: dict
    ):
        cid = _insert_ctf(
            db, title="Draft active CTF", status="draft", is_active=True
        )
        response = client.post(
            f"/api/v1/ctfs/{cid}/submit",
            json={"flag": "flag{test}"},
            headers=user_headers,
        )
        assert response.status_code == 404


class TestCtfStatistics:
    """GET /ctfs/statistics no debe 500."""

    def test_statistics_does_not_500(self, client: TestClient, db: Session):
        _insert_ctf(db, title="Public CTF", status="published")
        _insert_ctf(db, title="Draft CTF", status="draft")
        response = client.get("/api/v1/ctfs/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "solved" in data
        assert "by_level" in data
        assert "by_category" in data
        assert "by_platform" in data
        assert data["total"] >= 1


class TestFlagSubmitResponseCompat:
    """POST /ctfs/{id}/submit incluye is_correct y success."""

    def test_submit_response_includes_is_correct_and_success(
        self, client: TestClient, db: Session
    ):
        cid = _insert_ctf(db, title="Public CTF", status="published", is_active=True)
        response = client.post(
            f"/api/v1/ctfs/{cid}/submit",
            json={"flag": "flag{test}"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "success" in data
        assert "is_correct" in data
        assert data["success"] is True
        assert data["is_correct"] is True
        assert data.get("isCorrect") is True

    def test_submit_wrong_flag_includes_is_correct_false(
        self, client: TestClient, db: Session
    ):
        cid = _insert_ctf(db, title="Public CTF", status="published", is_active=True)
        response = client.post(
            f"/api/v1/ctfs/{cid}/submit",
            json={"flag": "flag{wrong}"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is False
        assert data["is_correct"] is False
