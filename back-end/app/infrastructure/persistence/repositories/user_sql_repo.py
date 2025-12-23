"""
Implementación SQL del repositorio de usuarios.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ....domain.entities.user import User
from ....domain.repositories.user_repo import UserRepository
from ..models.user_model import UserModel


class UserSqlRepository(UserRepository):
    """Implementación SQL del repositorio de usuarios."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, user: User) -> User:
        """Guarda un usuario (crear o actualizar)."""
        user_id = str(user.id)
        existing = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        
        if existing:
            # Actualizar
            existing.email = user.email
            existing.username = user.username
            existing.hashed_password = user.hashed_password
            existing.is_active = user.is_active
            existing.is_admin = user.is_admin
            existing.updated_at = user.updated_at
        else:
            # Crear
            db_user = UserModel(
                id=user_id,
                email=user.email,
                username=user.username,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at,
            )
            self.db.add(db_user)
        
        self.db.commit()
        return user
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Obtiene un usuario por su ID."""
        db_user = self.db.query(UserModel).filter(UserModel.id == str(user_id)).first()
        return self._to_entity(db_user) if db_user else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su email."""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_entity(db_user) if db_user else None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por su username."""
        db_user = self.db.query(UserModel).filter(UserModel.username == username).first()
        return self._to_entity(db_user) if db_user else None
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtiene todos los usuarios con paginación."""
        db_users = self.db.query(UserModel).offset(skip).limit(limit).all()
        return [self._to_entity(u) for u in db_users]
    
    def delete(self, user_id: UUID) -> bool:
        """Elimina un usuario por su ID."""
        result = self.db.query(UserModel).filter(UserModel.id == str(user_id)).delete()
        self.db.commit()
        return result > 0
    
    def exists_by_email(self, email: str) -> bool:
        """Verifica si existe un usuario con el email dado."""
        return self.db.query(UserModel).filter(UserModel.email == email).first() is not None
    
    def exists_by_username(self, username: str) -> bool:
        """Verifica si existe un usuario con el username dado."""
        return self.db.query(UserModel).filter(UserModel.username == username).first() is not None
    
    def _to_entity(self, model: UserModel) -> User:
        """Convierte un modelo a entidad de dominio."""
        from uuid import UUID as UUIDType
        return User(
            id=UUIDType(model.id),
            email=model.email,
            username=model.username,
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            is_admin=model.is_admin,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
