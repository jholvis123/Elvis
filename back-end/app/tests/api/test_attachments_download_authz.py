"""
Authz de GET /attachments/{id}/download: published público; draft/huérfano 404 salvo admin.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ...infrastructure.persistence.models.attachment_model import AttachmentModel
from ...infrastructure.persistence.models.ctf_model import CTFModel

PAYLOAD = "payload-for-download" + chr(10)
PAYLOAD_BYTES = b"payload-for-download" + bytes([10])


def _insert_ctf(db: Session, *, status: str) -> str:
    cid = str(uuid4())
    db.add(
        CTFModel(
            id=cid,
            title=f"CTF {status}",
            level="easy",
            category="web",
            platform="HackTheBox",
            description="desc",
            points=100,
            status=status,
            is_active=True,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    return cid


def _insert_file_attachment(
    db: Session,
    tmp_path: Path,
    *,
    ctf_id: Optional[str],
    name: str = "lab.txt",
) -> str:
    aid = str(uuid4())
    file_path = tmp_path / f"{aid}-{name}"
    file_path.write_text(PAYLOAD, encoding="utf-8")
    db.add(
        AttachmentModel(
            id=aid,
            name=name,
            type="file",
            ctf_id=ctf_id,
            file_path=str(file_path),
            size=file_path.stat().st_size,
            mime_type="text/plain",
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    return aid


class TestAttachmentDownloadAuthz:
    def test_anon_draft_parent_404(self, client: TestClient, db: Session, tmp_path: Path):
        ctf_id = _insert_ctf(db, status="draft")
        aid = _insert_file_attachment(db, tmp_path, ctf_id=ctf_id)
        r = client.get(f"/api/v1/attachments/{aid}/download")
        assert r.status_code == 404
        assert r.json()["detail"] == "Attachment not found"

    def test_anon_orphan_404(self, client: TestClient, db: Session, tmp_path: Path):
        aid = _insert_file_attachment(db, tmp_path, ctf_id=None)
        r = client.get(f"/api/v1/attachments/{aid}/download")
        assert r.status_code == 404

    def test_non_admin_draft_and_orphan_404(
        self, client: TestClient, db: Session, tmp_path: Path, user_headers: dict
    ):
        draft = _insert_ctf(db, status="draft")
        draft_aid = _insert_file_attachment(db, tmp_path, ctf_id=draft, name="d.txt")
        orphan_aid = _insert_file_attachment(db, tmp_path, ctf_id=None, name="o.txt")
        assert client.get(
            f"/api/v1/attachments/{draft_aid}/download", headers=user_headers
        ).status_code == 404
        assert client.get(
            f"/api/v1/attachments/{orphan_aid}/download", headers=user_headers
        ).status_code == 404

    def test_anon_published_parent_200(self, client: TestClient, db: Session, tmp_path: Path):
        ctf_id = _insert_ctf(db, status="published")
        aid = _insert_file_attachment(db, tmp_path, ctf_id=ctf_id)
        r = client.get(f"/api/v1/attachments/{aid}/download")
        assert r.status_code == 200
        assert r.content == PAYLOAD_BYTES

    def test_admin_draft_200(
        self, client: TestClient, db: Session, tmp_path: Path, admin_headers: dict
    ):
        ctf_id = _insert_ctf(db, status="draft")
        aid = _insert_file_attachment(db, tmp_path, ctf_id=ctf_id)
        r = client.get(f"/api/v1/attachments/{aid}/download", headers=admin_headers)
        assert r.status_code == 200

    def test_admin_orphan_200(
        self, client: TestClient, db: Session, tmp_path: Path, admin_headers: dict
    ):
        aid = _insert_file_attachment(db, tmp_path, ctf_id=None)
        r = client.get(f"/api/v1/attachments/{aid}/download", headers=admin_headers)
        assert r.status_code == 200

