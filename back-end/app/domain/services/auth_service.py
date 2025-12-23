"""
Servicio de dominio para autenticación.
Contiene reglas de negocio relacionadas con auth.
"""

from typing import Optional
from ..entities.user import User
from ..repositories.user_repo import UserRepository


class AuthService:
    """Servicio de dominio para lógica de autenticación."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def validate_unique_email(self, email: str) -> bool:
        """Valida que el email no esté en uso."""
        return not self.user_repository.exists_by_email(email)
    
    def validate_unique_username(self, username: str) -> bool:
        """Valida que el username no esté en uso."""
        return not self.user_repository.exists_by_username(username)
    
    def can_login(self, user: Optional[User]) -> bool:
        """Verifica si un usuario puede hacer login."""
        if user is None:
            return False
        return user.is_active
    
    def validate_registration(self, email: str, username: str) -> dict:
        """
        Valida los datos de registro.
        Retorna un diccionario con errores si los hay.
        """
        errors = {}
        
        if not self.validate_unique_email(email):
            errors["email"] = "Email already registered"
        
        if not self.validate_unique_username(username):
            errors["username"] = "Username already taken"
        
        if len(username) < 3:
            errors["username"] = "Username must be at least 3 characters"
        
        if len(username) > 50:
            errors["username"] = "Username must be at most 50 characters"
        
        return errors
