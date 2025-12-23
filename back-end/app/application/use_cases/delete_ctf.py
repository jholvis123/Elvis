"""
Caso de uso: Eliminar CTF.
"""

from uuid import UUID

from ...domain.repositories.ctf_repo import CTFRepository
from ...domain.repositories.writeup_repo import WriteupRepository


class DeleteCTFUseCase:
    """Caso de uso para eliminar un CTF."""
    
    def __init__(
        self,
        ctf_repository: CTFRepository,
        writeup_repository: WriteupRepository,
    ):
        self.ctf_repository = ctf_repository
        self.writeup_repository = writeup_repository
    
    def execute(self, ctf_id: UUID, force: bool = False) -> bool:
        """
        Ejecuta el caso de uso de eliminar un CTF.
        
        Args:
            ctf_id: ID del CTF a eliminar.
            force: Si es True, elimina también el writeup asociado.
            
        Returns:
            True si se eliminó, False si no existía.
            
        Raises:
            ValueError: Si tiene writeup y force=False.
        """
        # Verificar que existe
        ctf = self.ctf_repository.get_by_id(ctf_id)
        if not ctf:
            return False
        
        # Verificar si tiene writeup
        writeup = self.writeup_repository.get_by_ctf_id(ctf_id)
        if writeup and not force:
            raise ValueError(
                "CTF has an associated writeup. Use force=True to delete both."
            )
        
        # Eliminar writeup si existe y force=True
        if writeup and force:
            self.writeup_repository.delete(writeup.id)
        
        # Eliminar CTF
        return self.ctf_repository.delete(ctf_id)
