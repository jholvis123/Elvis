"""
Middleware de seguridad para agregar headers y rate limiting.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configurar rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])


async def security_headers_middleware(request: Request, call_next):
    """
    Middleware que agrega headers de seguridad a todas las respuestas.
    """
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Handler personalizado para errores de rate limit.
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Demasiadas solicitudes. Por favor, intenta más tarde.",
            "retry_after": exc.headers.get("Retry-After", "60")
        }
    )
