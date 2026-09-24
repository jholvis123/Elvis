"""
S3-compatible object storage adapter (AWS S3, Cloudflare R2, MinIO, etc.).
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from ...core.config import settings
from ...domain.services.storage_service import StorageService

_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".md": "text/markdown",
}


class S3Storage(StorageService):
    """StorageService backed by an S3-compatible bucket (e.g. Cloudflare R2)."""

    def __init__(
        self,
        *,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        client=None,
    ):
        self.bucket = bucket if bucket is not None else settings.S3_BUCKET
        if not self.bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_TYPE=s3")

        self.region = region if region is not None else (settings.S3_REGION or "auto")
        self.endpoint_url = (
            endpoint_url if endpoint_url is not None else settings.S3_ENDPOINT
        )
        access = access_key if access_key is not None else settings.S3_ACCESS_KEY
        secret = secret_key if secret_key is not None else settings.S3_SECRET_KEY

        if client is not None:
            self._client = client
        else:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url or None,
                aws_access_key_id=access,
                aws_secret_access_key=secret,
                region_name=self.region,
                config=Config(signature_version="s3v4"),
            )

    def _safe_subfolder(self, subfolder: str) -> str:
        if not subfolder:
            return ""
        cleaned = re.sub(r"[^\w\-/]", "_", subfolder)
        parts = [
            part
            for part in cleaned.split("/")
            if part and part not in ("..", ".")
        ]
        return "/".join(parts)

    def _object_key(self, relative_path: str) -> Optional[str]:
        """Normalize a relative path into a safe object key, or None if unsafe."""
        relative = Path(relative_path)
        if ".." in relative.parts:
            return None
        parts = [p for p in relative.parts if p and p not in (".", "..")]
        if not parts:
            return None
        return "/".join(parts)

    def save_file(self, file: BinaryIO, filename: str, subfolder: str = "") -> str:
        safe_name = Path(filename).name
        ext = os.path.splitext(safe_name)[1].lower()
        unique_name = f"{uuid.uuid4()}{ext}"

        safe_sub = self._safe_subfolder(subfolder)
        key = f"{safe_sub}/{unique_name}" if safe_sub else unique_name

        content_type = _CONTENT_TYPES.get(ext, "application/octet-stream")
        extra = {"ContentType": content_type}

        file.seek(0)
        self._client.upload_fileobj(
            file,
            self.bucket,
            key,
            ExtraArgs=extra,
        )

        return key

    def delete_file(self, file_path: str) -> bool:
        key = self._object_key(file_path)
        if not key:
            return False
        try:
            self._client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_file(self, file_path: str) -> Optional[bytes]:
        key = self._object_key(file_path)
        if not key:
            return None
        try:
            response = self._client.get_object(Bucket=self.bucket, Key=key)
            body = response["Body"].read()
            return body
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey", "NotFound"):
                return None
            raise
