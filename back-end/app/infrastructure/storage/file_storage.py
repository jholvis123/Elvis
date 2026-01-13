"""
Servicio de almacenamiento de archivos.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional
from uuid import uuid4
from datetime import datetime

from ...core.config import settings


class FileStorage:
    """Servicio para manejo de archivos en el sistema de archivos local."""
    
    # Caracteres permitidos en nombres de archivos (alfanuméricos, guiones, puntos, guiones bajos)
    SAFE_FILENAME_PATTERN = re.compile(r'^[\w\-. ]+$')
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.UPLOAD_DIR).resolve()
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
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitiza un nombre de archivo para prevenir path traversal.
        
        Args:
            filename: Nombre de archivo original.
            
        Returns:
            Nombre de archivo sanitizado.
        """
        # Obtener solo el nombre base (eliminar cualquier path)
        filename = Path(filename).name
        
        # Si está vacío después de limpiar, generar uno aleatorio
        if not filename:
            return f"unnamed_{uuid4().hex[:8]}"
        
        # Reemplazar caracteres no seguros
        safe_name = re.sub(r'[^\w\-. ]', '_', filename)
        
        # Asegurar que no empiece con punto (archivos ocultos)
        if safe_name.startswith('.'):
            safe_name = '_' + safe_name[1:]
        
        # Limitar longitud del nombre
        name_part = Path(safe_name).stem[:100]
        ext_part = Path(safe_name).suffix[:10]
        
        return name_part + ext_part
    
    def _validate_path(self, path: Path) -> bool:
        """
        Valida que un path esté dentro del directorio base.
        Previene path traversal attacks.
        
        Args:
            path: Path a validar.
            
        Returns:
            True si el path es válido y seguro.
        """
        try:
            resolved = path.resolve()
            return resolved.is_relative_to(self.base_path)
        except (ValueError, RuntimeError):
            return False
    
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
            
        Raises:
            ValueError: Si el archivo no es válido o hay un problema de seguridad.
        """
        # Sanitizar el nombre del archivo
        safe_filename = self._sanitize_filename(filename)
        
        # Validar extensión
        ext = Path(safe_filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension {ext} not allowed")
        
        # Validar tamaño
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds {settings.MAX_FILE_SIZE} bytes")
        
        # Sanitizar subfolder (solo permitir nombres simples)
        safe_subfolder = re.sub(r'[^\w\-/]', '_', subfolder)
        safe_subfolder = '/'.join(
            part for part in safe_subfolder.split('/') 
            if part and part not in ('..', '.')
        )
        
        # Generar nombre único
        unique_name = f"{uuid4().hex}_{safe_filename}"
        
        # Crear path completo y validar
        folder_path = self.base_path / safe_subfolder
        file_path = folder_path / unique_name
        
        # Validar que el path final está dentro del directorio base
        if not self._validate_path(file_path):
            raise ValueError("Invalid file path - security violation")
        
        # Crear directorio si no existe
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Guardar archivo
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(Path(safe_subfolder) / unique_name)
    
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
            Contenido del archivo o None si no existe o no es válido.
        """
        file_path = self.base_path / relative_path
        
        # Validar que el path está dentro del directorio base
        if not self._validate_path(file_path):
            return None
        
        if not file_path.exists() or not file_path.is_file():
            return None
        
        with open(file_path, "rb") as f:
            return f.read()
    
    def delete_file(self, relative_path: str) -> bool:
        """
        Elimina un archivo.
        
        Args:
            relative_path: Path relativo del archivo.
            
        Returns:
            True si se eliminó, False si no existía o no era válido.
        """
        file_path = self.base_path / relative_path
        
        # Validar que el path está dentro del directorio base
        if not self._validate_path(file_path):
            return False
        
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        
        return False
    
    def delete_folder(self, relative_path: str) -> bool:
        """
        Elimina una carpeta y su contenido.
        
        Args:
            relative_path: Path relativo de la carpeta.
            
        Returns:
            True si se eliminó, False si no existía o no era válido.
        """
        folder_path = self.base_path / relative_path
        
        # Validar que el path está dentro del directorio base
        if not self._validate_path(folder_path):
            return False
        
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
