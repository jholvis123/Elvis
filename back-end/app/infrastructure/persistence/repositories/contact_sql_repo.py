"""
Implementación SQL del repositorio de Contact.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ....domain.entities.contact import Contact, ContactStatus, ProjectType
from ....domain.repositories.contact_repo import ContactRepository
from ..models.contact_model import ContactModel


class ContactSqlRepository(ContactRepository):
    """Repositorio SQL para mensajes de contacto."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, contact: Contact) -> Contact:
        """Guarda un mensaje de contacto."""
        contact_id = str(contact.id)
        existing = self.db.query(ContactModel).filter(ContactModel.id == contact_id).first()
        
        if existing:
            existing.status = contact.status.value
            existing.read_at = contact.read_at
            existing.replied_at = contact.replied_at
        else:
            db_contact = ContactModel(
                id=contact_id,
                name=contact.name,
                email=contact.email,
                project_type=contact.project_type.value,
                message=contact.message,
                status=contact.status.value,
                ip_address=contact.ip_address,
                user_agent=contact.user_agent,
                created_at=contact.created_at,
            )
            self.db.add(db_contact)
        
        self.db.commit()
        return contact
    
    def get_by_id(self, contact_id: UUID) -> Optional[Contact]:
        """Obtiene un mensaje por su ID."""
        db_contact = self.db.query(ContactModel).filter(
            ContactModel.id == str(contact_id)
        ).first()
        return self._to_entity(db_contact) if db_contact else None
    
    def get_all(
        self,
        status: Optional[ContactStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Contact]:
        """Obtiene todos los mensajes con filtros opcionales."""
        query = self.db.query(ContactModel)
        
        if status:
            query = query.filter(ContactModel.status == status.value)
        
        query = query.order_by(ContactModel.created_at.desc())
        db_contacts = query.offset(skip).limit(limit).all()
        return [self._to_entity(c) for c in db_contacts]
    
    def get_pending(self, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Obtiene mensajes pendientes."""
        return self.get_all(status=ContactStatus.PENDING, skip=skip, limit=limit)
    
    def delete(self, contact_id: UUID) -> bool:
        """Elimina un mensaje."""
        result = self.db.query(ContactModel).filter(
            ContactModel.id == str(contact_id)
        ).delete()
        self.db.commit()
        return result > 0
    
    def count(self, status: Optional[ContactStatus] = None) -> int:
        """Cuenta mensajes con filtro opcional de estado."""
        query = self.db.query(ContactModel)
        if status:
            query = query.filter(ContactModel.status == status.value)
        return query.count()
    
    def _to_entity(self, model: ContactModel) -> Contact:
        """Convierte un modelo a entidad de dominio."""
        from uuid import UUID as UUIDType
        return Contact(
            id=UUIDType(model.id),
            name=model.name,
            email=model.email,
            project_type=ProjectType(model.project_type),
            message=model.message,
            status=ContactStatus(model.status),
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            created_at=model.created_at,
            read_at=model.read_at,
            replied_at=model.replied_at,
        )
