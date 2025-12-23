"""
Implementación SQL del repositorio de writeups.
"""

import json
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ....domain.entities.writeup import Writeup, WriteupStatus
from ....domain.repositories.writeup_repo import WriteupRepository
from ..models.writeup_model import WriteupModel


class WriteupSqlRepository(WriteupRepository):
    """Implementación SQL del repositorio de writeups."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, writeup: Writeup) -> Writeup:
        """Guarda un writeup (crear o actualizar)."""
        writeup_id = str(writeup.id)
        existing = self.db.query(WriteupModel).filter(WriteupModel.id == writeup_id).first()
        
        if existing:
            existing.title = writeup.title
            existing.content = writeup.content
            existing.summary = writeup.summary
            existing.tools_used = json.dumps(writeup.tools_used)
            existing.techniques = json.dumps(writeup.techniques)
            existing.attachments = json.dumps(writeup.attachments)
            existing.status = writeup.status.value
            existing.views = writeup.views
            existing.updated_at = writeup.updated_at
            existing.published_at = writeup.published_at
        else:
            db_writeup = WriteupModel(
                id=writeup_id,
                title=writeup.title,
                ctf_id=str(writeup.ctf_id),
                content=writeup.content,
                summary=writeup.summary,
                tools_used=json.dumps(writeup.tools_used),
                techniques=json.dumps(writeup.techniques),
                attachments=json.dumps(writeup.attachments),
                status=writeup.status.value,
                views=writeup.views,
                author_id=str(writeup.author_id) if writeup.author_id else None,
                created_at=writeup.created_at,
            )
            self.db.add(db_writeup)
        
        self.db.commit()
        return writeup
    
    def get_by_id(self, writeup_id: UUID) -> Optional[Writeup]:
        """Obtiene un writeup por su ID."""
        db_writeup = self.db.query(WriteupModel).filter(WriteupModel.id == str(writeup_id)).first()
        return self._to_entity(db_writeup) if db_writeup else None
    
    def get_by_ctf_id(self, ctf_id: UUID) -> Optional[Writeup]:
        """Obtiene el writeup asociado a un CTF."""
        db_writeup = self.db.query(WriteupModel).filter(WriteupModel.ctf_id == str(ctf_id)).first()
        return self._to_entity(db_writeup) if db_writeup else None
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WriteupStatus] = None,
    ) -> List[Writeup]:
        """Obtiene todos los writeups con paginación y filtros."""
        query = self.db.query(WriteupModel)
        
        if status:
            query = query.filter(WriteupModel.status == status.value)
        
        db_writeups = query.order_by(WriteupModel.created_at.desc()).offset(skip).limit(limit).all()
        return [self._to_entity(w) for w in db_writeups]
    
    def get_published(self, skip: int = 0, limit: int = 100) -> List[Writeup]:
        """Obtiene solo los writeups publicados."""
        return self.get_all(skip=skip, limit=limit, status=WriteupStatus.PUBLISHED)
    
    def get_by_author(self, author_id: UUID) -> List[Writeup]:
        """Obtiene writeups de un autor específico."""
        db_writeups = (
            self.db.query(WriteupModel)
            .filter(WriteupModel.author_id == str(author_id))
            .all()
        )
        return [self._to_entity(w) for w in db_writeups]
    
    def get_most_viewed(self, limit: int = 10) -> List[Writeup]:
        """Obtiene los writeups más vistos."""
        db_writeups = (
            self.db.query(WriteupModel)
            .filter(WriteupModel.status == "published")
            .order_by(WriteupModel.views.desc())
            .limit(limit)
            .all()
        )
        return [self._to_entity(w) for w in db_writeups]
    
    def search(self, query: str) -> List[Writeup]:
        """Busca writeups por título o contenido."""
        db_writeups = (
            self.db.query(WriteupModel)
            .filter(
                or_(
                    WriteupModel.title.ilike(f"%{query}%"),
                    WriteupModel.content.ilike(f"%{query}%"),
                    WriteupModel.summary.ilike(f"%{query}%"),
                )
            )
            .filter(WriteupModel.status == "published")
            .all()
        )
        return [self._to_entity(w) for w in db_writeups]
    
    def delete(self, writeup_id: UUID) -> bool:
        """Elimina un writeup por su ID."""
        result = self.db.query(WriteupModel).filter(WriteupModel.id == str(writeup_id)).delete()
        self.db.commit()
        return result > 0
    
    def count(self, status: Optional[WriteupStatus] = None) -> int:
        """Cuenta el número de writeups."""
        query = self.db.query(WriteupModel)
        if status:
            query = query.filter(WriteupModel.status == status.value)
        return query.count()
    
    def increment_views(self, writeup_id: UUID) -> bool:
        """Incrementa el contador de vistas de un writeup."""
        db_writeup = self.db.query(WriteupModel).filter(WriteupModel.id == str(writeup_id)).first()
        if db_writeup:
            db_writeup.views += 1
            self.db.commit()
            return True
        return False
    
    def _to_entity(self, model: WriteupModel) -> Writeup:
        """Convierte un modelo a entidad de dominio."""
        from uuid import UUID as UUIDType
        return Writeup(
            id=UUIDType(model.id),
            title=model.title,
            ctf_id=UUIDType(model.ctf_id),
            content=model.content,
            summary=model.summary,
            tools_used=json.loads(model.tools_used) if model.tools_used else [],
            techniques=json.loads(model.techniques) if model.techniques else [],
            attachments=json.loads(model.attachments) if model.attachments else [],
            status=WriteupStatus(model.status),
            views=model.views,
            author_id=UUIDType(model.author_id) if model.author_id else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
            published_at=model.published_at,
        )
