import os
import re
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

from ...domain.services.storage_service import StorageService
from ...core.config import settings


class FileSystemStorage(StorageService):
    def __init__(self, upload_dir: Optional[str] = None):
        # Leer settings en call-time (no default arg) para tests / monkeypatch
        self.upload_dir = Path(upload_dir if upload_dir is not None else settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _safe_subfolder(self, subfolder: str) -> str:
        """Sanitiza subfolder (sin path traversal)."""
        if not subfolder:
            return ""
        cleaned = re.sub(r"[^\w\-/]", "_", subfolder)
        parts = [
            part
            for part in cleaned.split("/")
            if part and part not in ("..", ".")
        ]
        return "/".join(parts)

    def save_file(self, file: BinaryIO, filename: str, subfolder: str = "") -> str:
        """
        Guarda el archivo en el sistema de archivos local.
        Retorna la ruta relativa del archivo (incluye subfolder/ si aplica).
        """
        safe_name = Path(filename).name
        ext = os.path.splitext(safe_name)[1]
        unique_name = f"{uuid.uuid4()}{ext}"

        safe_sub = self._safe_subfolder(subfolder)
        target_dir = self.upload_dir / safe_sub if safe_sub else self.upload_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / unique_name
        # Path traversal guard
        if not file_path.resolve().is_relative_to(self.upload_dir.resolve()):
            raise ValueError("Invalid file path - security violation")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

        if safe_sub:
            return str(Path(safe_sub) / unique_name)
        return unique_name

    def delete_file(self, filename: str) -> bool:
        """Elimina el archivo del sistema (ruta relativa al upload_dir)."""
        relative = Path(filename)
        if ".." in relative.parts:
            return False
        file_path = (self.upload_dir / relative).resolve()
        try:
            if not file_path.is_relative_to(self.upload_dir.resolve()):
                return False
        except (ValueError, RuntimeError):
            return False
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False


    def get_file(self, file_path: str) -> Optional[bytes]:
        """Lee bytes de una ruta relativa segura, o None si no existe."""
        resolved = self.resolve_path(file_path)
        if resolved is None:
            return None
        return resolved.read_bytes()

    def resolve_path(self, relative_path: str) -> Optional[Path]:
        """Resuelve una ruta relativa segura dentro de upload_dir, o None."""
        relative = Path(relative_path)
        if ".." in relative.parts:
            return None
        file_path = (self.upload_dir / relative).resolve()
        try:
            if not file_path.is_relative_to(self.upload_dir.resolve()):
                return None
        except (ValueError, RuntimeError):
            return None
        if file_path.exists() and file_path.is_file():
            return file_path
        return None
