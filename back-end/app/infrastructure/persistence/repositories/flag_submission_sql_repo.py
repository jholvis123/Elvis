"""
Implementación SQL del repositorio de FlagSubmission.
"""

from typing import List, Optional, Dict, Any
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
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene el ranking de usuarios por puntos de CTF.
        
        Returns:
            Lista de diccionarios con user_id, username, total_points, solved_count, rank
        """
        from sqlalchemy import func, distinct
        from ..models.user_model import UserModel
        from ..models.ctf_model import CTFModel
        
        # Subconsulta para obtener puntos por usuario
        # Solo contamos flags correctos y únicos por CTF
        subquery = (
            self.db.query(
                FlagSubmissionModel.user_id,
                func.sum(CTFModel.points).label('total_points'),
                func.count(distinct(FlagSubmissionModel.ctf_id)).label('solved_count')
            )
            .join(CTFModel, FlagSubmissionModel.ctf_id == CTFModel.id)
            .filter(
                FlagSubmissionModel.is_correct == True,
                FlagSubmissionModel.user_id.isnot(None)
            )
            .group_by(FlagSubmissionModel.user_id)
            .subquery()
        )
        
        # Query principal con join a usuarios
        results = (
            self.db.query(
                UserModel.id,
                UserModel.username,
                func.coalesce(subquery.c.total_points, 0).label('total_points'),
                func.coalesce(subquery.c.solved_count, 0).label('solved_count')
            )
            .outerjoin(subquery, UserModel.id == subquery.c.user_id)
            .filter(subquery.c.total_points > 0)  # Solo usuarios con puntos
            .order_by(func.coalesce(subquery.c.total_points, 0).desc())
            .limit(limit)
            .all()
        )
        
        leaderboard = []
        for rank, row in enumerate(results, start=1):
            leaderboard.append({
                'rank': rank,
                'user_id': row.id,
                'username': row.username,
                'total_points': int(row.total_points or 0),
                'solved_count': int(row.solved_count or 0)
            })
        
        return leaderboard
    
    def get_user_stats(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas de CTF de un usuario específico.
        
        Returns:
            Diccionario con total_points, solved_count, rank, solved_ctfs
        """
        from sqlalchemy import func, distinct
        from ..models.ctf_model import CTFModel
        from ..models.user_model import UserModel
        
        user_id_str = str(user_id)
        
        # Obtener CTFs resueltos por el usuario
        solved_ctfs_query = (
            self.db.query(
                CTFModel.id,
                CTFModel.title,
                CTFModel.points,
                CTFModel.category,
                CTFModel.level,
                FlagSubmissionModel.submitted_at.label('solved_at')
            )
            .join(FlagSubmissionModel, CTFModel.id == FlagSubmissionModel.ctf_id)
            .filter(
                FlagSubmissionModel.user_id == user_id_str,
                FlagSubmissionModel.is_correct == True
            )
            .order_by(FlagSubmissionModel.submitted_at.desc())
            .all()
        )
        
        # Calcular totales
        total_points = sum(ctf.points for ctf in solved_ctfs_query)
        solved_count = len(solved_ctfs_query)
        
        # Calcular ranking del usuario
        all_users_points = (
            self.db.query(
                FlagSubmissionModel.user_id,
                func.sum(CTFModel.points).label('points')
            )
            .join(CTFModel, FlagSubmissionModel.ctf_id == CTFModel.id)
            .filter(
                FlagSubmissionModel.is_correct == True,
                FlagSubmissionModel.user_id.isnot(None)
            )
            .group_by(FlagSubmissionModel.user_id)
            .order_by(func.sum(CTFModel.points).desc())
            .all()
        )
        
        user_rank = None
        for rank, row in enumerate(all_users_points, start=1):
            if row.user_id == user_id_str:
                user_rank = rank
                break
        
        # Obtener nombre de usuario
        user = self.db.query(UserModel).filter(UserModel.id == user_id_str).first()
        
        solved_ctfs = [
            {
                'id': str(ctf.id),
                'title': ctf.title,
                'points': ctf.points,
                'category': ctf.category,
                'level': ctf.level,
                'solved_at': ctf.solved_at.isoformat() if ctf.solved_at else None
            }
            for ctf in solved_ctfs_query
        ]
        
        return {
            'user_id': user_id_str,
            'username': user.username if user else 'Unknown',
            'total_points': total_points,
            'solved_count': solved_count,
            'rank': user_rank,
            'solved_ctfs': solved_ctfs
        }
    
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
