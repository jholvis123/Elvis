import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO
from ...domain.services.storage_service import StorageService
from ...core.config import settings

class FileSystemStorage(StorageService):
    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file: BinaryIO, filename: str) -> str:
        """
        Guarda el archivo en el sistema de archivos local.
        Retorna la ruta relativa del archivo.
        """
        # Generar nombre único para evitar colisiones
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        
        # Crear subdirectorios por fecha o tipo si fuera necesario
        # Por ahora plano para simplicidad
        file_path = self.upload_dir / unique_name
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)
            
        return str(unique_name)

    def delete_file(self, filename: str) -> bool:
        """Elimina el archivo del sistema."""
        file_path = self.upload_dir / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False
