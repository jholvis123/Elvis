"""
Servicio de almacenamiento de archivos.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from uuid import uuid4
from datetime import datetime

from ...core.config import settings


class FileStorage:
    """Servicio para manejo de archivos en el sistema de archivos local."""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.UPLOAD_DIR)
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Crea los directorios necesarios si no existen."""
        directories = [
            self.base_path,
            self.base_path / "writeups",
            self.base_path / "images",
            self.base_path / "attachments",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_file(
        self,
        file_content: bytes,
        filename: str,
        subfolder: str = "attachments",
    ) -> str:
        """
        Guarda un archivo y retorna su path relativo.
        
        Args:
            file_content: Contenido del archivo en bytes.
            filename: Nombre original del archivo.
            subfolder: Subcarpeta donde guardar.
            
        Returns:
            Path relativo del archivo guardado.
        """
        # Validar extensión
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension {ext} not allowed")
        
        # Validar tamaño
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds {settings.MAX_FILE_SIZE} bytes")
        
        # Generar nombre único
        unique_name = f"{uuid4().hex}_{filename}"
        
        # Crear path completo
        folder_path = self.base_path / subfolder
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / unique_name
        
        # Guardar archivo
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(Path(subfolder) / unique_name)
    
    def save_writeup_attachment(
        self,
        file_content: bytes,
        filename: str,
        writeup_id: str,
    ) -> str:
        """
        Guarda un archivo adjunto de writeup.
        
        Args:
            file_content: Contenido del archivo.
            filename: Nombre del archivo.
            writeup_id: ID del writeup.
            
        Returns:
            Path relativo del archivo.
        """
        subfolder = f"writeups/{writeup_id}"
        return self.save_file(file_content, filename, subfolder)
    
    def save_image(
        self,
        file_content: bytes,
        filename: str,
    ) -> str:
        """
        Guarda una imagen.
        
        Args:
            file_content: Contenido de la imagen.
            filename: Nombre del archivo.
            
        Returns:
            Path relativo de la imagen.
        """
        return self.save_file(file_content, filename, "images")
    
    def get_file(self, relative_path: str) -> Optional[bytes]:
        """
        Obtiene el contenido de un archivo.
        
        Args:
            relative_path: Path relativo del archivo.
            
        Returns:
            Contenido del archivo o None si no existe.
        """
        file_path = self.base_path / relative_path
        
        if not file_path.exists():
            return None
        
        with open(file_path, "rb") as f:
            return f.read()
    
    def delete_file(self, relative_path: str) -> bool:
        """
        Elimina un archivo.
        
        Args:
            relative_path: Path relativo del archivo.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        file_path = self.base_path / relative_path
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def delete_folder(self, relative_path: str) -> bool:
        """
        Elimina una carpeta y su contenido.
        
        Args:
            relative_path: Path relativo de la carpeta.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        folder_path = self.base_path / relative_path
        
        if folder_path.exists() and folder_path.is_dir():
            shutil.rmtree(folder_path)
            return True
        
        return False
    
    def get_file_url(self, relative_path: str) -> str:
        """
        Genera la URL para acceder a un archivo.
        
        Args:
            relative_path: Path relativo del archivo.
            
        Returns:
            URL del archivo.
        """
        return f"/files/{relative_path}"
    
    def list_files(self, subfolder: str = "") -> list:
        """
        Lista los archivos en una subcarpeta.
        
        Args:
            subfolder: Subcarpeta a listar.
            
        Returns:
            Lista de paths relativos.
        """
        folder_path = self.base_path / subfolder
        
        if not folder_path.exists():
            return []
        
        files = []
        for item in folder_path.iterdir():
            if item.is_file():
                files.append(str(Path(subfolder) / item.name))
        
        return files
