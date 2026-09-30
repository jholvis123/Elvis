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
        is_admin: bool = False,
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Valida un intento de flag.

        solved / solved_at solo los marca un admin (el owner).
        solved_count solo cuenta aciertos de visitantes que traen IP,
        deduplicados por user_id o, si el intento es anónimo, por esa IP.
        Sin IP no se incrementa, ni anónimo ni autenticado no-admin.

        Args:
            ctf_id: ID del CTF
            flag: Flag a validar
            user_id: ID del usuario (opcional)
            ip_address: IP del solicitante
            is_admin: True si el solicitante autenticado es administrador
            
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
        
        # Un usuario autenticado no vuelve a contar ni a reenviar el acierto.
        if user_id and self.submission_repository.has_user_solved(ctf_id, user_id):
            return False, "Ya has resuelto este reto", None
        
        # Validar formato de flag
        if not self._validate_flag_format(flag):
            return False, "Formato de flag inválido", None
        
        # Verificar flag
        normalized_flag = flag.strip()
        is_correct = ctf.verify_flag(normalized_flag)
        ip_address = self._normalized_ip(ip_address)
        
        # Decidir el contador ANTES de guardar: esta fila no puede contarse a sí misma.
        count_visitor_solve = (
            is_correct
            and not is_admin
            and self._is_new_visitor_solve(ctf_id, user_id, ip_address)
        )
        
        # Hash de la flag para almacenamiento seguro
        flag_hash = hashlib.sha256(normalized_flag.encode()).hexdigest()
        
        # Registrar intento (también los repetidos anónimos; el contador ya está decidido)
        submission = FlagSubmission(
            ctf_id=ctf_id,
            flag=flag_hash,  # Guardamos el hash, no el texto plano
            user_id=user_id,
            is_correct=is_correct,
            ip_address=ip_address,
        )
        self.submission_repository.save(submission)
        
        if is_correct:
            if is_admin:
                ctf.mark_as_solved()
                self.ctf_repository.save(ctf)
            elif count_visitor_solve:
                ctf.increment_solved_count()
                self.ctf_repository.save(ctf)
            
            return True, f"¡Correcto! +{ctf.points} puntos", ctf.points
        
        return False, "Flag incorrecta. Sigue intentando.", None

    def _is_new_visitor_solve(
        self,
        ctf_id: UUID,
        user_id: Optional[UUID],
        ip_address: Optional[str],
    ) -> bool:
        """True si este acierto de visitante debe incrementar solved_count.

        Sin IP no se cuenta, aunque haya user_id. Con IP, un usuario no
        repite conteo y un anónimo no repite conteo desde la misma IP.
        """
        if not ip_address:
            return False
        if user_id is not None:
            return not self.submission_repository.has_user_solved(ctf_id, user_id)
        return not self.submission_repository.has_anonymous_correct_from_ip(
            ctf_id, ip_address
        )

    @staticmethod
    def _normalized_ip(ip_address: Optional[str]) -> Optional[str]:
        if ip_address is None:
            return None
        cleaned = ip_address.strip()
        return cleaned or None
    
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
