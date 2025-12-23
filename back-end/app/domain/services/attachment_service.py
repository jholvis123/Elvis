"""
Servicio de dominio para Attachments.
Contiene la lógica de negocio para archivos adjuntos de CTFs.
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass

from ..entities.attachment import Attachment, AttachmentType
from ..entities.ctf import CTFCategory
from ..repositories.attachment_repo import AttachmentRepository


@dataclass
class AttachmentConfig:
    """Configuración de adjuntos por categoría."""
    allowed_types: List[AttachmentType]
    max_size: int  # bytes
    max_files: int
    allowed_extensions: List[str]
    allowed_mime_types: List[str]


class AttachmentService:
    """Servicio de dominio para lógica de adjuntos."""
    
    # Configuración por categoría de CTF
    CATEGORY_CONFIGS: Dict[str, AttachmentConfig] = {
        CTFCategory.WEB.value: AttachmentConfig(
            allowed_types=[AttachmentType.URL],
            max_size=0,
            max_files=3,
            allowed_extensions=[],
            allowed_mime_types=[],
        ),
        CTFCategory.CRYPTO.value: AttachmentConfig(
            allowed_types=[AttachmentType.FILE],
            max_size=5 * 1024 * 1024,  # 5MB
            max_files=3,
            allowed_extensions=[".txt", ".enc", ".bin", ".json", ".pem", ".key"],
            allowed_mime_types=["text/plain", "application/octet-stream", "application/json"],
        ),
        CTFCategory.STEGO.value: AttachmentConfig(
            allowed_types=[AttachmentType.FILE],
            max_size=50 * 1024 * 1024,  # 50MB
            max_files=5,
            allowed_extensions=[".png", ".jpg", ".jpeg", ".gif", ".bmp", ".wav", ".mp3", ".mp4"],
            allowed_mime_types=["image/*", "audio/*", "video/*"],
        ),
        CTFCategory.FORENSICS.value: AttachmentConfig(
            allowed_types=[AttachmentType.FILE],
            max_size=100 * 1024 * 1024,  # 100MB
            max_files=5,
            allowed_extensions=[".pcap", ".pcapng", ".raw", ".mem", ".img", ".dd", ".png", ".jpg", ".wav"],
            allowed_mime_types=["application/vnd.tcpdump.pcap", "application/octet-stream", "image/*", "audio/*"],
        ),
        CTFCategory.REVERSE.value: AttachmentConfig(
            allowed_types=[AttachmentType.FILE],
            max_size=50 * 1024 * 1024,  # 50MB
            max_files=2,
            allowed_extensions=[".exe", ".elf", ".bin", ".so", ".dll", ".apk", ".jar"],
            allowed_mime_types=["application/x-executable", "application/x-elf", "application/octet-stream"],
        ),
        CTFCategory.PWN.value: AttachmentConfig(
            allowed_types=[AttachmentType.FILE, AttachmentType.DOCKER],
            max_size=50 * 1024 * 1024,  # 50MB
            max_files=2,
            allowed_extensions=[".elf", ".bin", ".c", ".py"],
            allowed_mime_types=["application/x-executable", "application/x-elf", "application/octet-stream", "text/plain"],
        ),
        CTFCategory.MISC.value: AttachmentConfig(
            allowed_types=[AttachmentType.FILE, AttachmentType.URL],
            max_size=20 * 1024 * 1024,  # 20MB
            max_files=5,
            allowed_extensions=["*"],  # Cualquiera
            allowed_mime_types=["*/*"],
        ),
        CTFCategory.OSINT.value: AttachmentConfig(
            allowed_types=[AttachmentType.URL, AttachmentType.FILE],
            max_size=10 * 1024 * 1024,  # 10MB
            max_files=3,
            allowed_extensions=[".png", ".jpg", ".jpeg"],
            allowed_mime_types=["image/*"],
        ),
    }
    
    def __init__(self, attachment_repository: AttachmentRepository):
        self.attachment_repository = attachment_repository
    
    def get_config_for_category(self, category: str) -> Optional[AttachmentConfig]:
        """Obtiene la configuración para una categoría."""
        return self.CATEGORY_CONFIGS.get(category)
    
    def validate_file(
        self,
        filename: str,
        size: int,
        mime_type: str,
        category: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida un archivo según la configuración de la categoría.
        
        Returns:
            Tuple de (es_válido, mensaje_error)
        """
        config = self.get_config_for_category(category)
        if not config:
            return False, "Categoría inválida"
        
        # Verificar que la categoría permite archivos
        if AttachmentType.FILE not in config.allowed_types:
            return False, "Esta categoría no acepta archivos"
        
        # Validar tamaño
        if config.max_size > 0 and size > config.max_size:
            max_mb = config.max_size / (1024 * 1024)
            return False, f"Archivo demasiado grande. Máximo: {max_mb:.1f}MB"
        
        # Validar extensión
        if "*" not in config.allowed_extensions:
            ext = self._get_extension(filename)
            if ext.lower() not in [e.lower() for e in config.allowed_extensions]:
                return False, f"Extensión no permitida. Permitidas: {', '.join(config.allowed_extensions)}"
        
        # Validar MIME type
        if "*/*" not in config.allowed_mime_types:
            if not self._is_mime_type_allowed(mime_type, config.allowed_mime_types):
                return False, f"Tipo de archivo no permitido: {mime_type}"
        
        return True, None
    
    def validate_url(self, url: str, category: str) -> Tuple[bool, Optional[str]]:
        """
        Valida una URL según la configuración de la categoría.
        
        Returns:
            Tuple de (es_válida, mensaje_error)
        """
        config = self.get_config_for_category(category)
        if not config:
            return False, "Categoría inválida"
        
        # Verificar que la categoría permite URLs
        if AttachmentType.URL not in config.allowed_types:
            return False, "Esta categoría no acepta URLs"
        
        # Validar formato de URL
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return False, "URL inválida. Debe comenzar con http:// o https://"
        
        return True, None
    
    def get_ctf_attachments(self, ctf_id: UUID) -> List[Attachment]:
        """Obtiene todos los adjuntos de un CTF."""
        return self.attachment_repository.get_by_ctf_id(ctf_id)
    
    def _get_extension(self, filename: str) -> str:
        """Obtiene la extensión de un archivo."""
        if "." not in filename:
            return ""
        return "." + filename.rsplit(".", 1)[-1]
    
    def _is_mime_type_allowed(self, mime_type: str, allowed: List[str]) -> bool:
        """Verifica si un MIME type está permitido."""
        for allowed_type in allowed:
            if allowed_type.endswith("/*"):
                # Wildcard: image/* permite image/png, image/jpeg, etc.
                prefix = allowed_type[:-1]
                if mime_type.startswith(prefix):
                    return True
            elif allowed_type == mime_type:
                return True
        return False
    
    def requires_files(self, category: str) -> bool:
        """Verifica si una categoría requiere archivos."""
        config = self.get_config_for_category(category)
        return config is not None and AttachmentType.FILE in config.allowed_types
    
    def requires_url(self, category: str) -> bool:
        """Verifica si una categoría requiere URLs."""
        config = self.get_config_for_category(category)
        if not config:
            return False
        # Requiere URL si es el único tipo permitido
        return config.allowed_types == [AttachmentType.URL]
    
    def supports_docker(self, category: str) -> bool:
        """Verifica si una categoría soporta Docker."""
        config = self.get_config_for_category(category)
        return config is not None and AttachmentType.DOCKER in config.allowed_types
