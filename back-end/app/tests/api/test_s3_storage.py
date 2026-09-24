"""
Tests del adaptador S3-compatible (moto) y avatar en STORAGE_TYPE=s3.
No usa credenciales reales ni red.
"""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy.orm import Session

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)

BUCKET = "test-avatar-bucket"
REGION = "auto"
ENDPOINT = "https://example.r2.cloudflarestorage.com"


@pytest.fixture
def s3_bucket():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=BUCKET)
        yield client


@pytest.fixture
def s3_storage(s3_bucket):
    from ...infrastructure.storage.s3_storage import S3Storage

    return S3Storage(
        bucket=BUCKET,
        region=REGION,
        endpoint_url=ENDPOINT,
        access_key="testing",
        secret_key="testing",
        client=s3_bucket,
    )


class TestS3StorageUnit:
    def test_save_get_delete_roundtrip(self, s3_storage, s3_bucket):
        relative = s3_storage.save_file(
            BytesIO(PNG_1X1), filename="logo.png", subfolder="avatars"
        )
        assert relative.startswith("avatars/")
        assert relative.endswith(".png")

        data = s3_storage.get_file(relative)
        assert data == PNG_1X1

        assert s3_storage.delete_file(relative) is True
        assert s3_storage.get_file(relative) is None

    def test_get_missing_returns_none(self, s3_storage):
        assert s3_storage.get_file("avatars/missing.png") is None

    def test_rejects_path_traversal_on_get(self, s3_storage):
        assert s3_storage.get_file("../etc/passwd") is None
        assert s3_storage.delete_file("avatars/../../secret") is False

    def test_custom_endpoint_client_kwargs(self, s3_bucket):
        """Factory path builds a client with custom endpoint (R2-style)."""
        from ...infrastructure.storage.s3_storage import S3Storage

        storage = S3Storage(
            bucket=BUCKET,
            region="auto",
            endpoint_url=ENDPOINT,
            access_key="AKIA_TEST",
            secret_key="SECRET_TEST",
        )
        # moto still intercepts when under mock_aws if we use default endpoint;
        # here we only assert the adapter accepted R2-style kwargs without error.
        assert storage.bucket == BUCKET
        assert storage.endpoint_url == ENDPOINT
        assert storage.region == "auto"


@pytest.fixture
def s3_avatar_app(s3_storage, client: TestClient, monkeypatch: pytest.MonkeyPatch):
    from ...core.config import settings
    from ...main import app
    from ...api.dependencies import get_avatar_storage_service

    monkeypatch.setattr(settings, "STORAGE_TYPE", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", BUCKET)
    monkeypatch.setattr(settings, "S3_REGION", REGION)
    monkeypatch.setattr(settings, "S3_ENDPOINT", ENDPOINT)
    monkeypatch.setattr(settings, "S3_ACCESS_KEY", "testing")
    monkeypatch.setattr(settings, "S3_SECRET_KEY", "testing")

    app.dependency_overrides[get_avatar_storage_service] = lambda: s3_storage
    yield s3_storage
    app.dependency_overrides.pop(get_avatar_storage_service, None)


def _post_avatar(client: TestClient, headers: dict, *, filename: str, content: bytes):
    return client.post(
        "/api/v1/portfolio/avatar",
        headers=headers,
        files={"file": (filename, BytesIO(content), "application/octet-stream")},
    )


class TestPortfolioAvatarS3:
    def test_upload_get_delete_via_s3(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        s3_avatar_app,
        s3_bucket,
    ):
        res = _post_avatar(
            client, admin_headers, filename="logo.png", content=PNG_1X1
        )
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["avatar_url"].startswith("/api/v1/portfolio/avatar/file/")
        file_id = body["id"]

        # Object landed in bucket
        key = f"avatars/{file_id}"
        obj = s3_bucket.get_object(Bucket=BUCKET, Key=key)
        assert obj["Body"].read() == PNG_1X1

        # Public GET proxies bytes (no redirect)
        public = client.get(body["avatar_url"], follow_redirects=False)
        assert public.status_code == 200
        assert public.content == PNG_1X1
        assert "image/png" in public.headers.get("content-type", "")
        assert "public" in public.headers.get("cache-control", "").lower()
        assert public.headers.get("location") is None

        # Profile still has relative URL
        profile = client.get("/api/v1/portfolio/profile")
        assert profile.json()["avatar_url"] == body["avatar_url"]

        # DELETE removes object
        deleted = client.delete("/api/v1/portfolio/avatar", headers=admin_headers)
        assert deleted.status_code == 200
        assert deleted.json()["avatar_url"] is None
        assert client.get(body["avatar_url"]).status_code == 404

    def test_get_missing_object_404(
        self,
        client: TestClient,
        db: Session,
        s3_avatar_app,
    ):
        missing_id = f"{uuid4()}.png"
        res = client.get(f"/api/v1/portfolio/avatar/file/{missing_id}")
        assert res.status_code == 404

    def test_reject_path_traversal_id(
        self,
        client: TestClient,
        db: Session,
        s3_avatar_app,
    ):
        res = client.get("/api/v1/portfolio/avatar/file/../../etc/passwd")
        assert res.status_code == 404



class TestStorageTypeS3DoesNotBreakLocalUploads:
    """STORAGE_TYPE=s3 must NOT divert attachments/writeups away from local disk."""

    def test_attachment_upload_stays_local_when_storage_type_s3(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        s3_bucket,
    ):
        from ...core.config import settings
        from ...api.dependencies import get_avatar_storage_service, get_storage_service
        from ...infrastructure.storage.local_storage import FileSystemStorage
        from ...infrastructure.storage.s3_storage import S3Storage
        from ...main import app

        upload = tmp_path / "uploads"
        upload.mkdir()
        monkeypatch.setattr(settings, "STORAGE_TYPE", "s3")
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload))
        monkeypatch.setattr(settings, "S3_BUCKET", BUCKET)
        monkeypatch.setattr(settings, "S3_REGION", REGION)
        monkeypatch.setattr(settings, "S3_ENDPOINT", ENDPOINT)

        # Prove factory ignores STORAGE_TYPE for non-avatar storage
        assert isinstance(get_storage_service(), FileSystemStorage)

        s3 = S3Storage(
            bucket=BUCKET,
            region=REGION,
            endpoint_url=ENDPOINT,
            access_key="testing",
            secret_key="testing",
            client=s3_bucket,
        )
        # Keep avatar on S3 mock; attachments must use real get_storage_service (local)
        app.dependency_overrides[get_avatar_storage_service] = lambda: s3
        try:
            res = client.post(
                "/api/v1/attachments/upload",
                headers=admin_headers,
                files={"file": ("note.txt", BytesIO(b"hello-attachment"), "text/plain")},
            )
            assert res.status_code in (200, 201), res.text
            files = [p for p in upload.rglob("*") if p.is_file()]
            assert files, f"expected local files under {upload}, got {list(upload.rglob('*'))}"
            assert any(p.read_bytes() == b"hello-attachment" for p in files)
        finally:
            app.dependency_overrides.pop(get_avatar_storage_service, None)

    def test_writeup_image_upload_returns_local_uploads_path(
        self,
        client: TestClient,
        db: Session,
        admin_headers: dict,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        s3_bucket,
    ):
        from ...core.config import settings
        from ...api.dependencies import get_avatar_storage_service, get_storage_service
        from ...infrastructure.storage.local_storage import FileSystemStorage
        from ...infrastructure.storage.s3_storage import S3Storage
        from ...main import app

        upload = tmp_path / "uploads"
        upload.mkdir()
        monkeypatch.setattr(settings, "STORAGE_TYPE", "s3")
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload))
        monkeypatch.setattr(settings, "S3_BUCKET", BUCKET)

        assert isinstance(get_storage_service(), FileSystemStorage)

        s3 = S3Storage(
            bucket=BUCKET,
            region=REGION,
            endpoint_url=ENDPOINT,
            access_key="testing",
            secret_key="testing",
            client=s3_bucket,
        )
        app.dependency_overrides[get_avatar_storage_service] = lambda: s3
        try:
            res = client.post(
                "/api/v1/writeups/upload-image",
                headers=admin_headers,
                files={"file": ("shot.png", BytesIO(PNG_1X1), "image/png")},
            )
            assert res.status_code in (200, 201), res.text
            body = res.json()
            url = body.get("url") or body.get("image_url") or ""
            assert url.startswith("/uploads/"), body
            files = [p for p in upload.rglob("*") if p.is_file()]
            assert files, f"expected local writeup image under {upload}"
        finally:
            app.dependency_overrides.pop(get_avatar_storage_service, None)
