"""
Tests del adaptador S3-compatible (moto) y avatar en STORAGE_TYPE=s3.
No usa credenciales reales ni red.
"""

from io import BytesIO
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
    from ...api.dependencies import get_storage_service

    monkeypatch.setattr(settings, "STORAGE_TYPE", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET", BUCKET)
    monkeypatch.setattr(settings, "S3_REGION", REGION)
    monkeypatch.setattr(settings, "S3_ENDPOINT", ENDPOINT)
    monkeypatch.setattr(settings, "S3_ACCESS_KEY", "testing")
    monkeypatch.setattr(settings, "S3_SECRET_KEY", "testing")

    app.dependency_overrides[get_storage_service] = lambda: s3_storage
    yield s3_storage
    app.dependency_overrides.pop(get_storage_service, None)


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
