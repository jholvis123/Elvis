"""
Servicio de protección CSRF.
Genera y valida tokens CSRF para proteger contra ataques Cross-Site Request Forgery.
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status

from ...core.config import settings


class CSRFService:
    """
    Servicio para protección contra CSRF.
    
    Implementa el patrón Double Submit Cookie:
    1. Token CSRF se envía en una cookie (accesible desde JS)
    2. El frontend debe incluir el mismo token en el header X-CSRF-Token
    3. El backend verifica que ambos coincidan
    """
    
    TOKEN_LENGTH = 32
    
    def __init__(self):
        self.secret_key = settings.CSRF_SECRET_KEY or settings.SECRET_KEY
    
    def generate_token(self, user_id: Optional[str] = None) -> str:
        """
        Genera un token CSRF seguro.
        
        Args:
            user_id: ID del usuario (opcional, para tokens vinculados)
            
        Returns:
            Token CSRF
        """
        # Generar token aleatorio
        random_bytes = secrets.token_bytes(self.TOKEN_LENGTH)
        timestamp = str(int(datetime.utcnow().timestamp()))
        
        # Crear payload
        payload = f"{random_bytes.hex()}:{timestamp}"
        if user_id:
            payload = f"{payload}:{user_id}"
        
        # Firmar con HMAC
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{payload}:{signature}"
    
    def validate_token(
        self,
        token: str,
        max_age_minutes: int = 60,
        user_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Valida un token CSRF.
        
        Args:
            token: Token a validar
            max_age_minutes: Edad máxima del token en minutos
            user_id: ID del usuario esperado (opcional)
            
        Returns:
            Tuple de (es_válido, mensaje_error)
        """
        if not token:
            return False, "CSRF token missing"
        
        try:
            parts = token.split(":")
            if len(parts) < 3:
                return False, "Invalid CSRF token format"
            
            # Extraer componentes
            if len(parts) == 3:
                random_hex, timestamp, signature = parts
                token_user_id = None
            else:
                random_hex, timestamp, token_user_id, signature = parts
            
            # Reconstruir payload y verificar firma
            payload = f"{random_hex}:{timestamp}"
            if token_user_id:
                payload = f"{payload}:{token_user_id}"
            
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False, "Invalid CSRF token signature"
            
            # Verificar edad del token
            token_time = datetime.fromtimestamp(int(timestamp))
            if datetime.utcnow() - token_time > timedelta(minutes=max_age_minutes):
                return False, "CSRF token expired"
            
            # Verificar usuario si se especificó
            if user_id and token_user_id != user_id:
                return False, "CSRF token user mismatch"
            
            return True, ""
            
        except (ValueError, TypeError) as e:
            return False, f"CSRF token validation error: {str(e)}"
    
    def validate_request(self, request: Request) -> None:
        """
        Valida la protección CSRF de una petición.
        
        Compara el token de la cookie con el del header.
        
        Args:
            request: Request de FastAPI
            
        Raises:
            HTTPException: Si la validación CSRF falla
        """
        # Obtener token de cookie
        cookie_token = request.cookies.get("csrf_token")
        
        # Obtener token de header
        header_token = request.headers.get("X-CSRF-Token")
        
        if not cookie_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF cookie missing",
            )
        
        if not header_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF header missing",
            )
        
        # Comparar tokens (deben ser idénticos en Double Submit Cookie)
        if not hmac.compare_digest(cookie_token, header_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token mismatch",
            )
        
        # Validar el token en sí
        is_valid, error = self.validate_token(cookie_token)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error,
            )


# Instancia global
csrf_service = CSRFService()
