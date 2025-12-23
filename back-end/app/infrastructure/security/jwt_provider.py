"""
Proveedor de JWT para autenticación.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel

from ...core.config import settings


class TokenData(BaseModel):
    """Datos extraídos de un token."""
    user_id: str
    token_type: str
    exp: datetime


class JWTProvider:
    """Proveedor de tokens JWT."""
    
    def __init__(
        self,
        secret_key: str = settings.SECRET_KEY,
        algorithm: str = settings.ALGORITHM,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Crea un token de acceso.
        
        Args:
            user_id: ID del usuario.
            expires_delta: Tiempo de expiración personalizado.
            
        Returns:
            Token JWT.
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Crea un token de refresco.
        
        Args:
            user_id: ID del usuario.
            expires_delta: Tiempo de expiración personalizado.
            
        Returns:
            Token JWT de refresco.
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verifica y decodifica un token.
        
        Args:
            token: Token JWT a verificar.
            
        Returns:
            Datos del token o None si es inválido.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            user_id = payload.get("sub")
            token_type = payload.get("type")
            exp = payload.get("exp")
            
            if user_id is None:
                return None
            
            return TokenData(
                user_id=user_id,
                token_type=token_type or "access",
                exp=datetime.fromtimestamp(exp) if exp else datetime.utcnow(),
            )
            
        except JWTError:
            return None
    
    def verify_access_token(self, token: str) -> Optional[TokenData]:
        """
        Verifica que sea un token de acceso válido.
        
        Args:
            token: Token a verificar.
            
        Returns:
            Datos del token o None si es inválido.
        """
        token_data = self.verify_token(token)
        
        if token_data and token_data.token_type == "access":
            return token_data
        
        return None
    
    def verify_refresh_token(self, token: str) -> Optional[TokenData]:
        """
        Verifica que sea un token de refresco válido.
        
        Args:
            token: Token a verificar.
            
        Returns:
            Datos del token o None si es inválido.
        """
        token_data = self.verify_token(token)
        
        if token_data and token_data.token_type == "refresh":
            return token_data
        
        return None
