"""
Implementación SQL del repositorio de FlagSubmission.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ....domain.entities.flag_submission import FlagSubmission
from ....domain.repositories.flag_submission_repo import FlagSubmissionRepository
from ..models.flag_submission_model import FlagSubmissionModel


class FlagSubmissionSqlRepository(FlagSubmissionRepository):
    """Repositorio SQL para envíos de flags."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, submission: FlagSubmission) -> FlagSubmission:
        """Guarda un envío de flag."""
        db_submission = FlagSubmissionModel(
            id=str(submission.id),
            ctf_id=str(submission.ctf_id),
            user_id=str(submission.user_id) if submission.user_id else None,
            flag=submission.flag,
            is_correct=submission.is_correct,
            ip_address=submission.ip_address,
            submitted_at=submission.submitted_at,
        )
        self.db.add(db_submission)
        self.db.commit()
        return submission
    
    def get_by_ctf_id(self, ctf_id: UUID, skip: int = 0, limit: int = 100) -> List[FlagSubmission]:
        """Obtiene envíos por CTF."""
        db_submissions = self.db.query(FlagSubmissionModel).filter(
            FlagSubmissionModel.ctf_id == str(ctf_id)
        ).order_by(
            FlagSubmissionModel.submitted_at.desc()
        ).offset(skip).limit(limit).all()
        return [self._to_entity(s) for s in db_submissions]
    
    def get_successful_by_ctf_id(self, ctf_id: UUID) -> List[FlagSubmission]:
        """Obtiene intentos exitosos de un CTF."""
        db_submissions = self.db.query(FlagSubmissionModel).filter(
            FlagSubmissionModel.ctf_id == str(ctf_id),
            FlagSubmissionModel.is_correct == True
        ).order_by(
            FlagSubmissionModel.submitted_at.desc()
        ).all()
        return [self._to_entity(s) for s in db_submissions]
    
    def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[FlagSubmission]:
        """Obtiene envíos por usuario."""
        db_submissions = self.db.query(FlagSubmissionModel).filter(
            FlagSubmissionModel.user_id == str(user_id)
        ).order_by(
            FlagSubmissionModel.submitted_at.desc()
        ).offset(skip).limit(limit).all()
        return [self._to_entity(s) for s in db_submissions]
    
    def has_user_solved(self, ctf_id: UUID, user_id: UUID) -> bool:
        """Verifica si un usuario ya resolvió un CTF."""
        return self.db.query(FlagSubmissionModel).filter(
            FlagSubmissionModel.ctf_id == str(ctf_id),
            FlagSubmissionModel.user_id == str(user_id),
            FlagSubmissionModel.is_correct == True
        ).first() is not None
    
    def count_solvers(self, ctf_id: UUID) -> int:
        """Cuenta usuarios únicos que resolvieron un CTF."""
        from sqlalchemy import func
        result = self.db.query(
            func.count(func.distinct(FlagSubmissionModel.user_id))
        ).filter(
            FlagSubmissionModel.ctf_id == str(ctf_id),
            FlagSubmissionModel.is_correct == True
        ).scalar()
        return result or 0
    
    def get_recent_submissions(
        self,
        ctf_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[FlagSubmission]:
        """Obtiene envíos recientes."""
        query = self.db.query(FlagSubmissionModel)
        
        if ctf_id:
            query = query.filter(FlagSubmissionModel.ctf_id == str(ctf_id))
        
        db_submissions = query.order_by(
            FlagSubmissionModel.submitted_at.desc()
        ).limit(limit).all()
        return [self._to_entity(s) for s in db_submissions]
    
    def _to_entity(self, model: FlagSubmissionModel) -> FlagSubmission:
        """Convierte modelo a entidad de dominio."""
        from uuid import UUID as UUIDType
        return FlagSubmission(
            id=UUIDType(model.id),
            ctf_id=UUIDType(model.ctf_id),
            user_id=UUIDType(model.user_id) if model.user_id else None,
            flag=model.flag,
            is_correct=model.is_correct,
            ip_address=model.ip_address,
            submitted_at=model.submitted_at,
        )
