"""
Storage module - Manejo de archivos (local filesystem y S3-compatible).
"""

from .file_storage import FileStorage
from .local_storage import FileSystemStorage
from .s3_storage import S3Storage

__all__ = ["FileStorage", "FileSystemStorage", "S3Storage"]
