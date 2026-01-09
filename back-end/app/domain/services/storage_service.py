from abc import ABC, abstractmethod
from typing import BinaryIO

class StorageService(ABC):
    @abstractmethod
    def save_file(self, file: BinaryIO, filename: str) -> str:
        """Saves a file and returns its URL/Path."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Deletes a file."""
        pass
