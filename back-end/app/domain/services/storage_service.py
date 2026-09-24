from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class StorageService(ABC):
    @abstractmethod
    def save_file(self, file: BinaryIO, filename: str, subfolder: str = "") -> str:
        """Saves a file and returns its relative path (may include subfolder/)."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Deletes a file (relative path from upload dir / object key)."""
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> Optional[bytes]:
        """Returns file bytes for a relative path / object key, or None if missing."""
        pass
