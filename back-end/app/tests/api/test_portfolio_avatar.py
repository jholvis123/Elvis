"""
Tests de upload/delete/GET de avatar del portfolio.
"""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Minimal valid magic-byte payloads
PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def avatar_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, client: TestClient):
    """Redirige storage a tmp_path para no escribir en el cwd del repo."""
    upload = tmp_path / "uploads"
    upload.mkdir()
    monkeypatch.setenv("UPLOAD_DIR", str(upload))

    from ...core.config import settings
    from ...main import app
    from ...api.dependencies import get_avatar_storage_service
    from ...infrastructure.storage.local_storage import FileSystemStorage

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload))

    def _override_storage():
        return FileSystemStorage(upload_dir=str(upload))

    app.dependency_overrides[get_avatar_storage_service] = _override_storage
    yield upload
    app.dependency_overrides.pop(get_avatar_storage_service, None)


def _post_avatar(client: TestClient, headers: dict, *, filename: str, content: bytes):
    return client.post(
        "/api/v1/portfolio/avatar",
        headers=headers,
        files={"file": (filename, BytesIO(content), "application/octet-stream")},
    )


class TestPortfolioAvatarUpload:
    def test_upload_ok_updates_profile_and_public_get(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        avatar_upload_dir: Path,
    ):
        res = _post_avatar(
            client, admin_headers, filename="logo.png", content=PNG_1X1
        )
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["content_type"] == "image/png"
        assert body["size"] == len(PNG_1X1)
        assert body["avatar_url"].startswith("/api/v1/portfolio/avatar/file/")
        assert body["id"] == body["filename"]
        assert body["id"].endswith(".png")

        # Archivo en disco
        on_disk = avatar_upload_dir / "avatars" / body["id"]
        assert on_disk.is_file()
        assert on_disk.read_bytes() == PNG_1X1

        # Perfil refleja avatar_url
        profile = client.get("/api/v1/portfolio/profile")
        assert profile.status_code == 200
        assert profile.json()["avatar_url"] == body["avatar_url"]

        # GET público sin auth
        public = client.get(body["avatar_url"])
        assert public.status_code == 200
        assert public.content == PNG_1X1
        assert "image/png" in public.headers.get("content-type", "")

    def test_reject_exe(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        avatar_upload_dir: Path,
    ):
        # MZ header (PE) with .exe extension
        res = _post_avatar(
            client,
            admin_headers,
            filename="malware.exe",
            content=b"MZ" + b"\x00" * 64,
        )
        assert res.status_code == 400
        assert "not allowed" in res.json()["detail"].lower() or "extension" in res.json()[
            "detail"
        ].lower()

    def test_reject_pdf_extension(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        avatar_upload_dir: Path,
    ):
        res = _post_avatar(
            client,
            admin_headers,
            filename="doc.pdf",
            content=b"%PDF-1.4 fake",
        )
        assert res.status_code == 400

    def test_reject_oversized(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        avatar_upload_dir: Path,
    ):
        # Valid PNG header + pad over 2MB
        big = PNG_1X1 + (b"\x00" * (2 * 1024 * 1024 + 1))
        res = _post_avatar(
            client, admin_headers, filename="big.png", content=big
        )
        assert res.status_code == 400
        assert "size" in res.json()["detail"].lower() or "maximum" in res.json()[
            "detail"
        ].lower()

    def test_auth_required(
        self,
        client: TestClient,
        db: Session,
        avatar_upload_dir: Path,
    ):
        res = _post_avatar(
            client, {}, filename="logo.png", content=PNG_1X1
        )
        assert res.status_code in (401, 403)

    def test_non_admin_forbidden(
        self,
        client: TestClient,
        db: Session,
        user_headers: dict,
        avatar_upload_dir: Path,
    ):
        res = _post_avatar(
            client, user_headers, filename="logo.png", content=PNG_1X1
        )
        assert res.status_code == 403

    def test_delete_clears_url_and_file(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        avatar_upload_dir: Path,
    ):
        up = _post_avatar(
            client, admin_headers, filename="logo.png", content=PNG_1X1
        )
        assert up.status_code == 201
        file_id = up.json()["id"]
        path = avatar_upload_dir / "avatars" / file_id
        assert path.is_file()

        deleted = client.delete("/api/v1/portfolio/avatar", headers=admin_headers)
        assert deleted.status_code == 200
        assert deleted.json()["avatar_url"] is None
        assert not path.exists()

        profile = client.get("/api/v1/portfolio/profile")
        assert profile.json()["avatar_url"] is None

        assert client.get(f"/api/v1/portfolio/avatar/file/{file_id}").status_code == 404

    def test_put_profile_https_avatar_fallback(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        avatar_upload_dir: Path,
    ):
        """PUT /portfolio/profile sigue aceptando avatar_url https externos."""
        https_url = "https://cdn.example.com/elvis-avatar.png"
        res = client.put(
            "/api/v1/portfolio/profile",
            headers=admin_headers,
            json={
                "name": "Elvis",
                "title": "Dev",
                "bio": "x",
                "avatar_url": https_url,
                "roles": ["Dev"],
                "stack_items": ["Python"],
                "about_points": ["a"],
                "highlights": [],
                "social_links": {},
            },
        )
        assert res.status_code == 200, res.text
        assert res.json()["avatar_url"] == https_url
        assert client.get("/api/v1/portfolio/profile").json()["avatar_url"] == https_url

    def test_reject_wrong_magic_with_png_ext(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        avatar_upload_dir: Path,
    ):
        # .png name but PDF content
        res = _post_avatar(
            client,
            admin_headers,
            filename="fake.png",
            content=b"%PDF-1.7 not an image",
        )
        assert res.status_code == 400
