"""
Entidad CTF - Capture The Flag challenges.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum
import hashlib
import re


class CTFLevel(str, Enum):
    """Niveles de dificultad de CTF."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    INSANE = "insane"


class CTFCategory(str, Enum):
    """Categorías de CTF."""
    WEB = "web"
    PWN = "pwn"
    REVERSE = "reverse"
    CRYPTO = "crypto"
    FORENSICS = "forensics"
    MISC = "misc"
    OSINT = "osint"
    STEGO = "stego"


class CTFStatus(str, Enum):
    """Estados de un CTF."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


from .attachment import Attachment

@dataclass
class CTF:
    """Entidad de dominio para retos CTF."""
    
    title: str
    level: CTFLevel
    category: CTFCategory
    platform: str
    id: UUID = field(default_factory=uuid4)
    description: Optional[str] = None
    points: int = 0
    solved: bool = False
    solved_at: Optional[datetime] = None
    machine_os: Optional[str] = None
    # Campos alineados con frontend
    skills: List[str] = field(default_factory=list)  # Antes: tags
    hints: List[str] = field(default_factory=list)   # Pistas para resolver
    flag_hash: Optional[str] = None                   # Hash de la flag (o patrón regex)
    is_flag_regex: bool = False                       # Si es True, flag_hash guarda el patrón regex
    author: Optional[str] = None                      # Autor del reto (texto libre)
    created_by_id: Optional[UUID] = None              # ID del usuario creador (sistema)
    updated_by_id: Optional[UUID] = None              # ID del usuario actualizador (sistema)
    solved_count: int = 0                             # Número de soluciones
    is_active: bool = True                            # Si el reto está activo
    status: CTFStatus = CTFStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    attachments: List[Attachment] = field(default_factory=list)
    
    def mark_as_solved(self) -> None:
        """Marca el CTF como resuelto."""
        self.solved = True
        self.solved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_solved_count(self) -> None:
        """Incrementa el contador de soluciones."""
        self.solved_count += 1
        self.updated_at = datetime.utcnow()
    
    def set_flag(self, flag: str, is_regex: bool = False) -> None:
        """Establece la flag (se almacena como hash o regex)."""
        self.is_flag_regex = is_regex
        if is_regex:
            # Si es regex, guardamos el patrón tal cual (cuidado con esto en BD abierta)
            self.flag_hash = flag
        else:
            # Si es estática, guardamos el hash
            self.flag_hash = hashlib.sha256(flag.encode()).hexdigest()
        self.updated_at = datetime.utcnow()
    
    def verify_flag(self, flag: str) -> bool:
        """Verifica si una flag es correcta."""
        if not self.flag_hash:
            return False
            
        if self.is_flag_regex:
            # Verificación mediante Regex
            try:
                return bool(re.match(self.flag_hash, flag))
            except re.error:
                return False
        else:
            # Verificación mediante Hash
            return hashlib.sha256(flag.encode()).hexdigest() == self.flag_hash
    
    def add_hint(self, hint: str) -> None:
        """Añade una pista al CTF."""
        if hint not in self.hints:
            self.hints.append(hint)
            self.updated_at = datetime.utcnow()
    
    def add_skill(self, skill: str) -> None:
        """Añade una habilidad/skill al CTF."""
        if skill not in self.skills:
            self.skills.append(skill)
            self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Desactiva el CTF."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activa el CTF."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def publish(self) -> None:
        """Publica el CTF."""
        self.status = CTFStatus.PUBLISHED
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archiva el CTF."""
        self.status = CTFStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    @property
    def is_published(self) -> bool:
        """Verifica si el CTF está publicado."""
        return self.status == CTFStatus.PUBLISHED
    
    @property
    def is_available(self) -> bool:
        """Verifica si el CTF está disponible (publicado y activo)."""
        return self.is_published and self.is_active
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CTF):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
