"""
Servicio de dominio para Writeups.
Contiene reglas de negocio relacionadas con writeups.
"""

from typing import Optional
from uuid import UUID
from ..entities.writeup import Writeup, WriteupStatus
from ..entities.ctf import CTF
from ..repositories.writeup_repo import WriteupRepository
from ..repositories.ctf_repo import CTFRepository


class WriteupService:
    """Servicio de dominio para lógica de writeups."""
    
    def __init__(
        self,
        writeup_repository: WriteupRepository,
        ctf_repository: CTFRepository,
    ):
        self.writeup_repository = writeup_repository
        self.ctf_repository = ctf_repository
    
    def can_create_writeup(self, ctf_id: UUID) -> tuple[bool, Optional[str]]:
        """
        Verifica si se puede crear un writeup para un CTF.
        Retorna (puede_crear, mensaje_error).
        """
        # Si no hay CTF asociado, se puede crear (writeup independiente)
        if ctf_id is None:
            return True, None
            
        # Verificar que el CTF existe
        ctf = self.ctf_repository.get_by_id(ctf_id)
        if not ctf:
            return False, "CTF not found"
        
        # Verificar que no existe ya un writeup
        existing = self.writeup_repository.get_by_ctf_id(ctf_id)
        if existing:
            return False, "Writeup already exists for this CTF"
        
        return True, None
    
    def can_publish(self, writeup: Writeup) -> tuple[bool, Optional[str]]:
        """
        Verifica si un writeup puede ser publicado.
        Retorna (puede_publicar, mensaje_error).
        """
        if not writeup.title or len(writeup.title.strip()) == 0:
            return False, "Writeup must have a title"
        
        if not writeup.content or len(writeup.content.strip()) < 100:
            return False, "Writeup content must be at least 100 characters"
        
        if writeup.status == WriteupStatus.PUBLISHED:
            return False, "Writeup is already published"
        
        # Verificar que el CTF asociado está publicado
        ctf = self.ctf_repository.get_by_id(writeup.ctf_id)
        if ctf and not ctf.is_published:
            return False, "Associated CTF must be published first"
        
        return True, None
    
    def validate_writeup_content(self, content: str) -> dict:
        """
        Valida el contenido de un writeup.
        Retorna un diccionario con errores si los hay.
        """
        errors = {}
        
        if not content or len(content.strip()) == 0:
            errors["content"] = "Content is required"
        elif len(content) < 100:
            errors["content"] = "Content must be at least 100 characters"
        elif len(content) > 100000:
            errors["content"] = "Content must be at most 100,000 characters"
        
        return errors
    
    def calculate_read_time(self, content: str) -> int:
        """Calcula el tiempo estimado de lectura en minutos."""
        words = len(content.split())
        # Promedio de lectura: 200 palabras por minuto
        return max(1, words // 200)
    
    def extract_tools_from_content(self, content: str) -> list[str]:
        """
        Extrae herramientas mencionadas en el contenido.
        Busca patrones comunes de herramientas de CTF.
        """
        common_tools = [
            "nmap", "gobuster", "dirb", "dirbuster", "nikto",
            "burp", "burpsuite", "sqlmap", "hydra", "john",
            "hashcat", "metasploit", "msfconsole", "netcat", "nc",
            "wireshark", "tcpdump", "ghidra", "ida", "gdb",
            "pwntools", "binwalk", "steghide", "stegsolve",
            "exiftool", "strings", "file", "ltrace", "strace",
            "radare2", "r2", "objdump", "checksec", "ropper",
            "volatility", "autopsy", "foremost", "photorec",
        ]
        
        content_lower = content.lower()
        found_tools = []
        
        for tool in common_tools:
            if tool in content_lower:
                found_tools.append(tool)
        
        return found_tools
