"""
Implementación SQL del repositorio de CTFs.
"""

import json
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ....domain.entities.ctf import CTF, CTFLevel, CTFCategory, CTFStatus
from ....domain.repositories.ctf_repo import CTFRepository
from ..models.ctf_model import CTFModel


class CTFSqlRepository(CTFRepository):
    """Implementación SQL del repositorio de CTFs."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, ctf: CTF) -> CTF:
        """Guarda un CTF (crear o actualizar)."""
        ctf_id = str(ctf.id)
        existing = self.db.query(CTFModel).filter(CTFModel.id == ctf_id).first()
        
        if existing:
            existing.title = ctf.title
            existing.level = ctf.level.value
            existing.category = ctf.category.value
            existing.platform = ctf.platform
            existing.description = ctf.description
            existing.points = ctf.points
            existing.solved = ctf.solved
            existing.solved_at = ctf.solved_at
            existing.machine_os = ctf.machine_os
            existing.skills = json.dumps(ctf.skills)
            existing.hints = json.dumps(ctf.hints)
            existing.flag_hash = ctf.flag_hash
            existing.author = ctf.author
            existing.solved_count = ctf.solved_count
            existing.is_active = ctf.is_active
            existing.status = ctf.status.value
            existing.updated_at = ctf.updated_at
            
            # Actualizar adjuntos si es necesario (simplificado: recrear)
            # Nota: Esto es destructivo, idealmente se debería comparar
            if ctf.attachments:
                # Eliminar existentes para evitar duplicados si la lógica de negocio lo requiere,
                # pero aquí asumimos que ctf.attachments es la verdad absoluta.
                # Sin embargo, SQLAlchemy gestiona la colección.
                # Una estrategia simple es limpiar y agregar.
                # existing.attachments.clear() # Cuidado con orphans
                pass 
                # TODO: Implementar lógica de actualización de adjuntos más robusta si se requiere edición
        else:
            # Crear modelos de adjuntos
            from ..models.attachment_model import AttachmentModel
            attachment_models = []
            for att in ctf.attachments:
                att_model = AttachmentModel(
                    id=str(att.id),
                    name=att.name,
                    type=att.type.value,
                    url=att.url,
                    size=att.size,
                    mime_type=att.mime_type,
                    ctf_id=ctf_id
                )
                attachment_models.append(att_model)

            db_ctf = CTFModel(
                id=ctf_id,
                title=ctf.title,
                level=ctf.level.value,
                category=ctf.category.value,
                platform=ctf.platform,
                description=ctf.description,
                points=ctf.points,
                solved=ctf.solved,
                solved_at=ctf.solved_at,
                machine_os=ctf.machine_os,
                skills=json.dumps(ctf.skills),
                hints=json.dumps(ctf.hints),
                flag_hash=ctf.flag_hash,
                author=ctf.author,
                solved_count=ctf.solved_count,
                is_active=ctf.is_active,
                status=ctf.status.value,
                created_at=ctf.created_at,
                attachments=attachment_models
            )
            self.db.add(db_ctf)
        
        self.db.commit()
        return ctf
    
    def get_by_id(self, ctf_id: UUID) -> Optional[CTF]:
        """Obtiene un CTF por su ID."""
        db_ctf = self.db.query(CTFModel).filter(CTFModel.id == str(ctf_id)).first()
        return self._to_entity(db_ctf) if db_ctf else None
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CTFStatus] = None,
    ) -> List[CTF]:
        """Obtiene todos los CTFs con paginación y filtros."""
        query = self.db.query(CTFModel)
        
        if status:
            query = query.filter(CTFModel.status == status.value)
        
        db_ctfs = query.order_by(CTFModel.created_at.desc()).offset(skip).limit(limit).all()
        return [self._to_entity(c) for c in db_ctfs]
    
    def get_by_level(self, level: CTFLevel) -> List[CTF]:
        """Obtiene CTFs por nivel de dificultad."""
        db_ctfs = (
            self.db.query(CTFModel)
            .filter(CTFModel.level == level.value)
            .filter(CTFModel.status == "published")
            .all()
        )
        return [self._to_entity(c) for c in db_ctfs]
    
    def get_by_category(self, category: CTFCategory) -> List[CTF]:
        """Obtiene CTFs por categoría."""
        db_ctfs = (
            self.db.query(CTFModel)
            .filter(CTFModel.category == category.value)
            .filter(CTFModel.status == "published")
            .all()
        )
        return [self._to_entity(c) for c in db_ctfs]
    
    def get_by_platform(self, platform: str) -> List[CTF]:
        """Obtiene CTFs por plataforma."""
        db_ctfs = (
            self.db.query(CTFModel)
            .filter(CTFModel.platform.ilike(f"%{platform}%"))
            .filter(CTFModel.status == "published")
            .all()
        )
        return [self._to_entity(c) for c in db_ctfs]
    
    def get_published(self, skip: int = 0, limit: int = 100) -> List[CTF]:
        """Obtiene solo los CTFs publicados."""
        return self.get_all(skip=skip, limit=limit, status=CTFStatus.PUBLISHED)
    
    def get_solved(self) -> List[CTF]:
        """Obtiene los CTFs resueltos."""
        db_ctfs = (
            self.db.query(CTFModel)
            .filter(CTFModel.solved == True)
            .all()
        )
        return [self._to_entity(c) for c in db_ctfs]
    
    def search(self, query: str) -> List[CTF]:
        """Busca CTFs por título o skills."""
        db_ctfs = (
            self.db.query(CTFModel)
            .filter(
                or_(
                    CTFModel.title.ilike(f"%{query}%"),
                    CTFModel.skills.ilike(f"%{query}%"),
                    CTFModel.description.ilike(f"%{query}%"),
                )
            )
            .filter(CTFModel.status == "published")
            .filter(CTFModel.is_active == True)
            .all()
        )
        return [self._to_entity(c) for c in db_ctfs]
    
    def delete(self, ctf_id: UUID) -> bool:
        """Elimina un CTF por su ID."""
        result = self.db.query(CTFModel).filter(CTFModel.id == str(ctf_id)).delete()
        self.db.commit()
        return result > 0
    
    def count(
        self,
        status: Optional[CTFStatus] = None,
        category: Optional[CTFCategory] = None,
    ) -> int:
        """Cuenta el número de CTFs con filtros opcionales."""
        query = self.db.query(CTFModel)
        
        if status:
            query = query.filter(CTFModel.status == status.value)
        
        if category:
            query = query.filter(CTFModel.category == category.value)
        
        return query.count()
    
    def get_statistics(self) -> dict:
        """Obtiene estadísticas de CTFs (por nivel, categoría, etc.)."""
        all_ctfs = self.db.query(CTFModel).filter(CTFModel.status == "published").all()
        
        by_level = {}
        by_category = {}
        by_platform = {}
        
        total_points = 0
        earned_points = 0
        
        for ctf in all_ctfs:
            total_points += ctf.points
            if ctf.solved:
                earned_points += ctf.points
                
            # Por nivel
            by_level[ctf.level] = by_level.get(ctf.level, 0) + 1
            # Por categoría
            by_category[ctf.category] = by_category.get(ctf.category, 0) + 1
            # Por plataforma
            by_platform[ctf.platform] = by_platform.get(ctf.platform, 0) + 1
        
        return {
            "by_level": by_level,
            "by_category": by_category,
            "by_platform": by_platform,
            "total_points": total_points,
            "earned_points": earned_points,
        }
    
    def _to_entity(self, model: CTFModel) -> CTF:
        """Convierte un modelo a entidad de dominio."""
        from uuid import UUID as UUIDType
        # Mapear adjuntos
        from ....domain.entities.attachment import Attachment, AttachmentType
        attachments = [
            Attachment(
                id=UUIDType(att.id),
                name=att.name,
                type=AttachmentType(att.type),
                url=att.url,
                size=att.size,
                mime_type=att.mime_type,
                ctf_id=UUIDType(att.ctf_id)
            )
            for att in model.attachments
        ]

        return CTF(
            id=UUIDType(model.id),
            title=model.title,
            level=CTFLevel(model.level),
            category=CTFCategory(model.category),
            platform=model.platform,
            description=model.description,
            points=model.points,
            solved=model.solved,
            solved_at=model.solved_at,
            machine_os=model.machine_os,
            skills=json.loads(model.skills) if model.skills else [],
            hints=json.loads(model.hints) if model.hints else [],
            flag_hash=model.flag_hash,
            author=model.author,
            solved_count=model.solved_count or 0,
            is_active=model.is_active if model.is_active is not None else True,
            status=CTFStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            attachments=attachments
        )
