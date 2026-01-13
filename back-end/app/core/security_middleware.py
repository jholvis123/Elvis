"""
Middleware de seguridad para agregar headers y rate limiting.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import hashlib


def get_rate_limit_key(request: Request) -> str:
    """
    Genera una clave única para rate limiting.
    Combina IP + User-Agent para evitar algunos bypasses.
    """
    ip = get_remote_address(request)
    user_agent = request.headers.get("User-Agent", "")
    
    # Crear hash para no exponer datos sensibles
    combined = f"{ip}:{user_agent}"
    return hashlib.md5(combined.encode()).hexdigest()[:16]


# Configurar rate limiter con límites por defecto
limiter = Limiter(
    key_func=get_rate_limit_key, 
    default_limits=["100/minute", "1000/hour"],
    storage_uri="memory://",  # En producción usar Redis
    strategy="fixed-window",
)

# Rate limits específicos por tipo de endpoint
RATE_LIMITS = {
    "login": "5/minute",        # Login muy limitado
    "register": "3/minute",     # Registro muy limitado
    "password_reset": "3/hour", # Reset de password
    "flag_submit": "10/minute", # Envío de flags
    "upload": "10/minute",      # Subida de archivos
    "api_write": "30/minute",   # Operaciones de escritura
    "api_read": "100/minute",   # Operaciones de lectura
}


async def security_headers_middleware(request: Request, call_next):
    """
    Middleware que agrega headers de seguridad a todas las respuestas.
    """
    response = await call_next(request)
    
    # Security headers básicos
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # HSTS solo en producción (HTTPS)
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # CSP más permisivo para desarrollo, más estricto en producción
    # En desarrollo permitimos 'unsafe-inline' para facilitar debugging
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    
    # Prevenir caching de respuestas sensibles
    if request.url.path.startswith("/api/v1/auth"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    
    return response


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Handler personalizado para errores de rate limit.
    """
    retry_after = exc.headers.get("Retry-After", "60") if exc.headers else "60"
    
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Demasiadas solicitudes. Por favor, intenta más tarde.",
            "retry_after": retry_after
        },
        headers={"Retry-After": str(retry_after)}
    )
