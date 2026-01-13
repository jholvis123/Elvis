"""
Servicio de validación de archivos.
Valida archivos usando magic bytes y otras técnicas.
"""

from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple
import struct

from ...core.config import settings


# Magic bytes conocidos para tipos de archivo comunes
# Formato: {extension: [(offset, bytes), ...]}
MAGIC_BYTES: Dict[str, List[Tuple[int, bytes]]] = {
    # Imágenes
    '.png': [(0, b'\x89PNG\r\n\x1a\n')],
    '.jpg': [(0, b'\xff\xd8\xff')],
    '.jpeg': [(0, b'\xff\xd8\xff')],
    '.gif': [(0, b'GIF87a'), (0, b'GIF89a')],
    '.webp': [(0, b'RIFF'), (8, b'WEBP')],
    '.bmp': [(0, b'BM')],
    
    # Documentos
    '.pdf': [(0, b'%PDF')],
    
    # Archivos comprimidos
    '.zip': [(0, b'PK\x03\x04'), (0, b'PK\x05\x06'), (0, b'PK\x07\x08')],
    '.gz': [(0, b'\x1f\x8b')],
    '.tar': [(257, b'ustar')],  # En formato POSIX
    '.7z': [(0, b'7z\xbc\xaf\x27\x1c')],
    '.rar': [(0, b'Rar!\x1a\x07')],
    
    # Ejecutables
    '.exe': [(0, b'MZ')],
    '.elf': [(0, b'\x7fELF')],
    
    # Redes/Forense
    '.pcap': [(0, b'\xd4\xc3\xb2\xa1'), (0, b'\xa1\xb2\xc3\xd4')],
    '.pcapng': [(0, b'\x0a\x0d\x0d\x0a')],
    
    # Virtualización
    '.iso': [(0x8001, b'CD001'), (0x8801, b'CD001'), (0x9001, b'CD001')],
    '.ova': [(0, b'PK\x03\x04')],  # Es básicamente un ZIP
    '.qcow2': [(0, b'QFI\xfb')],
    
    # Código/Texto (no tienen magic bytes específicos, se validan de otra forma)
    '.txt': [],
    '.md': [],
    '.py': [],
    '.c': [],
    '.cpp': [],
    '.js': [],
    '.html': [],
    '.css': [],
    '.json': [],
    '.xml': [],
    '.yaml': [],
    '.yml': [],
    
    # Java
    '.jar': [(0, b'PK\x03\x04')],  # Es un ZIP
    '.apk': [(0, b'PK\x03\x04')],  # También es un ZIP
    
    # Binarios
    '.bin': [],  # Sin magic específico
}

# Extensiones que son texto plano (no necesitan validación de magic bytes)
TEXT_EXTENSIONS = {
    '.txt', '.md', '.py', '.c', '.cpp', '.js', '.html', '.css',
    '.json', '.xml', '.yaml', '.yml', '.h', '.hpp', '.java',
    '.rb', '.go', '.rs', '.ts', '.sh', '.bat', '.ps1',
}

# Tipos MIME peligrosos que nunca deberían permitirse ejecutar
DANGEROUS_MIME_TYPES = {
    'application/x-msdownload',
    'application/x-msdos-program',
    'application/x-sh',
    'application/x-shellscript',
}


class FileValidationError(Exception):
    """Error de validación de archivo."""
    pass


class FileValidator:
    """Servicio para validación segura de archivos."""
    
    def __init__(self, allowed_extensions: Optional[List[str]] = None, max_size: Optional[int] = None):
        self.allowed_extensions = set(allowed_extensions or settings.ALLOWED_EXTENSIONS)
        self.max_size = max_size or settings.MAX_FILE_SIZE
    
    def validate_extension(self, filename: str) -> str:
        """
        Valida que la extensión del archivo esté permitida.
        
        Args:
            filename: Nombre del archivo.
            
        Returns:
            La extensión en minúsculas.
            
        Raises:
            FileValidationError: Si la extensión no está permitida.
        """
        ext = Path(filename).suffix.lower()
        if not ext:
            raise FileValidationError("File must have an extension")
        
        if ext not in self.allowed_extensions:
            raise FileValidationError(f"File extension '{ext}' is not allowed")
        
        return ext
    
    def validate_magic_bytes(self, file: BinaryIO, extension: str) -> bool:
        """
        Valida que el contenido del archivo coincida con su extensión.
        
        Args:
            file: Archivo binario a validar.
            extension: Extensión declarada del archivo.
            
        Returns:
            True si es válido.
            
        Raises:
            FileValidationError: Si el contenido no coincide con la extensión.
        """
        ext_lower = extension.lower()
        
        # Archivos de texto no tienen magic bytes específicos
        if ext_lower in TEXT_EXTENSIONS:
            return True
        
        # Obtener magic bytes esperados
        expected_magic = MAGIC_BYTES.get(ext_lower, [])
        
        # Si no hay magic bytes definidos para esta extensión, permitir
        if not expected_magic:
            return True
        
        # Guardar posición actual
        original_position = file.tell()
        
        try:
            # Verificar cada posible magic byte
            for offset, magic in expected_magic:
                file.seek(offset)
                header = file.read(len(magic))
                
                if header == magic:
                    return True
            
            # Ninguno coincidió
            raise FileValidationError(
                f"File content does not match expected format for '{ext_lower}'"
            )
        
        finally:
            # Restaurar posición original
            file.seek(original_position)
    
    def validate_size(self, size: int) -> None:
        """
        Valida el tamaño del archivo.
        
        Args:
            size: Tamaño en bytes.
            
        Raises:
            FileValidationError: Si el archivo es muy grande.
        """
        if size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            raise FileValidationError(f"File size exceeds maximum allowed ({max_mb:.1f} MB)")
        
        if size == 0:
            raise FileValidationError("File is empty")
    
    def validate_mime_type(self, mime_type: str) -> None:
        """
        Valida que el tipo MIME no sea peligroso.
        
        Args:
            mime_type: Tipo MIME del archivo.
            
        Raises:
            FileValidationError: Si el tipo MIME es peligroso.
        """
        if mime_type.lower() in DANGEROUS_MIME_TYPES:
            raise FileValidationError(f"MIME type '{mime_type}' is not allowed")
    
    def validate_file(
        self, 
        file: BinaryIO, 
        filename: str, 
        size: int,
        mime_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Realiza validación completa de un archivo.
        
        Args:
            file: Archivo binario.
            filename: Nombre del archivo.
            size: Tamaño en bytes.
            mime_type: Tipo MIME declarado (opcional).
            
        Returns:
            Tupla (extensión, mime_type_seguro).
            
        Raises:
            FileValidationError: Si alguna validación falla.
        """
        # 1. Validar extensión
        extension = self.validate_extension(filename)
        
        # 2. Validar tamaño
        self.validate_size(size)
        
        # 3. Validar MIME type si se proporciona
        if mime_type:
            self.validate_mime_type(mime_type)
        
        # 4. Validar magic bytes
        self.validate_magic_bytes(file, extension)
        
        # Determinar MIME type seguro basado en extensión
        safe_mime = self._get_safe_mime_type(extension)
        
        return extension, safe_mime
    
    def _get_safe_mime_type(self, extension: str) -> str:
        """
        Obtiene un MIME type seguro basado en la extensión.
        
        Args:
            extension: Extensión del archivo.
            
        Returns:
            MIME type seguro.
        """
        mime_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.pdf': 'application/pdf',
            '.zip': 'application/zip',
            '.gz': 'application/gzip',
            '.tar': 'application/x-tar',
            '.7z': 'application/x-7z-compressed',
            '.rar': 'application/vnd.rar',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.html': 'text/html',
            '.css': 'text/css',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.pcap': 'application/vnd.tcpdump.pcap',
            '.pcapng': 'application/x-pcapng',
            '.iso': 'application/x-iso9660-image',
            '.exe': 'application/x-msdownload',
            '.elf': 'application/x-executable',
        }
        
        return mime_map.get(extension.lower(), 'application/octet-stream')


# Instancia global para uso fácil
file_validator = FileValidator()
