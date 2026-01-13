"""
Servicio de cookies seguras para autenticación.
Maneja la creación y validación de cookies HttpOnly para tokens JWT.
"""

from datetime import timedelta
from typing import Optional
from fastapi import Response, Request
from fastapi.responses import JSONResponse

from ...core.config import settings


class CookieService:
    """
    Servicio para gestión segura de cookies de autenticación.
    
    Implementa:
    - Cookies HttpOnly (no accesibles desde JavaScript)
    - Secure flag (solo HTTPS en producción)
    - SameSite (protección CSRF)
    """
    
    ACCESS_TOKEN_COOKIE = "access_token"
    REFRESH_TOKEN_COOKIE = "refresh_token"
    CSRF_TOKEN_COOKIE = "csrf_token"
    
    def __init__(self):
        self.secure = settings.COOKIE_SECURE
        self.samesite = settings.COOKIE_SAMESITE
        self.domain = settings.COOKIE_DOMAIN
    
    def set_access_token_cookie(
        self,
        response: Response,
        token: str,
        expires_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    ) -> None:
        """
        Establece la cookie del access token.
        
        Args:
            response: Respuesta FastAPI
            token: Token JWT de acceso
            expires_minutes: Minutos hasta expiración
        """
        response.set_cookie(
            key=self.ACCESS_TOKEN_COOKIE,
            value=token,
            max_age=expires_minutes * 60,
            httponly=True,  # No accesible desde JavaScript
            secure=self.secure,  # Solo HTTPS en producción
            samesite=self.samesite,  # Protección CSRF
            domain=self.domain,
            path="/",
        )
    
    def set_refresh_token_cookie(
        self,
        response: Response,
        token: str,
        expires_days: int = settings.REFRESH_TOKEN_EXPIRE_DAYS,
    ) -> None:
        """
        Establece la cookie del refresh token.
        
        Args:
            response: Respuesta FastAPI
            token: Token JWT de refresco
            expires_days: Días hasta expiración
        """
        response.set_cookie(
            key=self.REFRESH_TOKEN_COOKIE,
            value=token,
            max_age=expires_days * 24 * 60 * 60,
            httponly=True,
            secure=self.secure,
            samesite=self.samesite,
            domain=self.domain,
            path="/api/v1/auth",  # Solo accesible en rutas de auth
        )
    
    def set_csrf_token_cookie(
        self,
        response: Response,
        token: str,
    ) -> None:
        """
        Establece la cookie CSRF (accesible desde JavaScript para enviar en headers).
        
        Args:
            response: Respuesta FastAPI
            token: Token CSRF
        """
        response.set_cookie(
            key=self.CSRF_TOKEN_COOKIE,
            value=token,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=False,  # Debe ser accesible desde JS para enviarlo en headers
            secure=self.secure,
            samesite=self.samesite,
            domain=self.domain,
            path="/",
        )
    
    def clear_auth_cookies(self, response: Response) -> None:
        """
        Elimina todas las cookies de autenticación.
        
        Args:
            response: Respuesta FastAPI
        """
        response.delete_cookie(
            key=self.ACCESS_TOKEN_COOKIE,
            path="/",
            domain=self.domain,
        )
        response.delete_cookie(
            key=self.REFRESH_TOKEN_COOKIE,
            path="/api/v1/auth",
            domain=self.domain,
        )
        response.delete_cookie(
            key=self.CSRF_TOKEN_COOKIE,
            path="/",
            domain=self.domain,
        )
    
    def get_access_token_from_cookie(self, request: Request) -> Optional[str]:
        """
        Obtiene el access token desde la cookie.
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Token o None si no existe
        """
        return request.cookies.get(self.ACCESS_TOKEN_COOKIE)
    
    def get_refresh_token_from_cookie(self, request: Request) -> Optional[str]:
        """
        Obtiene el refresh token desde la cookie.
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Token o None si no existe
        """
        return request.cookies.get(self.REFRESH_TOKEN_COOKIE)
    
    def get_csrf_token_from_header(self, request: Request) -> Optional[str]:
        """
        Obtiene el token CSRF desde el header X-CSRF-Token.
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Token CSRF o None
        """
        return request.headers.get("X-CSRF-Token")


# Instancia global
cookie_service = CookieService()
