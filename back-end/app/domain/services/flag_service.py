"""
Servicio de dominio para validación de flags.
Contiene la lógica de negocio para submit de flags en CTFs.
"""

from typing import Optional, Tuple
from uuid import UUID
from datetime import datetime
import hashlib

from ..entities.ctf import CTF
from ..entities.flag_submission import FlagSubmission
from ..repositories.ctf_repo import CTFRepository
from ..repositories.flag_submission_repo import FlagSubmissionRepository


class FlagService:
    """Servicio de dominio para lógica de validación de flags."""
    
    def __init__(
        self,
        ctf_repository: CTFRepository,
        submission_repository: FlagSubmissionRepository,
    ):
        self.ctf_repository = ctf_repository
        self.submission_repository = submission_repository
    
    def submit_flag(
        self,
        ctf_id: UUID,
        flag: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Valida un intento de flag.
        
        Args:
            ctf_id: ID del CTF
            flag: Flag a validar
            user_id: ID del usuario (opcional)
            ip_address: IP del solicitante
            
        Returns:
            Tuple de (éxito, mensaje, puntos_ganados)
        """
        # Obtener CTF
        ctf = self.ctf_repository.get_by_id(ctf_id)
        if not ctf:
            return False, "CTF no encontrado", None
        
        # Verificar que el CTF está disponible
        if not ctf.is_available:
            return False, "Este reto no está disponible", None
        
        # Verificar si el usuario ya resolvió este CTF
        if user_id and self.submission_repository.has_user_solved(ctf_id, user_id):
            return False, "Ya has resuelto este reto", None
        
        # Validar formato de flag
        if not self._validate_flag_format(flag):
            return False, "Formato de flag inválido", None
        
        # Verificar flag
        is_correct = ctf.verify_flag(flag.strip())
        
        # Hash de la flag para almacenamiento seguro
        flag_hash = hashlib.sha256(flag.strip().encode()).hexdigest()
        
        # Registrar intento
        submission = FlagSubmission(
            ctf_id=ctf_id,
            flag=flag_hash,  # Guardamos el hash, no el texto plano
            user_id=user_id,
            is_correct=is_correct,
            ip_address=ip_address,
        )
        self.submission_repository.save(submission)
        
        if is_correct:
            # Marcar CTF como resuelto y actualizar contador
            ctf.mark_as_solved()
            ctf.increment_solved_count()
            self.ctf_repository.save(ctf)
            
            return True, f"¡Correcto! +{ctf.points} puntos", ctf.points
        
        return False, "Flag incorrecta. Sigue intentando.", None
    
    def _validate_flag_format(self, flag: str) -> bool:
        """Valida el formato básico de una flag."""
        if not flag or len(flag.strip()) == 0:
            return False
        
        # Formato típico: flag{...}
        flag = flag.strip()
        if not (flag.startswith("flag{") and flag.endswith("}")):
            return False
        
        # Verificar contenido entre llaves
        content = flag[5:-1]  # Quitar flag{ y }
        if len(content) == 0:
            return False
        
        return True
    
    def get_user_solved_ctfs(self, user_id: UUID) -> list[UUID]:
        """Obtiene lista de CTFs resueltos por un usuario."""
        submissions = self.submission_repository.get_by_user_id(user_id)
        return [s.ctf_id for s in submissions if s.is_correct]
    
    def get_ctf_solvers_count(self, ctf_id: UUID) -> int:
        """Obtiene el número de usuarios que resolvieron un CTF."""
        return self.submission_repository.count_solvers(ctf_id)
