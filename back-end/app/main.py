"""
Portfolio Backend - Clean Architecture + Hexagonal

Punto de entrada principal de la aplicación FastAPI.
"""

import traceback
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .core.database import engine, get_db
from .core.logging import logger
from .core.security_middleware import (
    limiter,
    security_headers_middleware,
    csrf_protect_middleware,
    rate_limit_exceeded_handler,
)
from .api.routers import (
    auth_router,
    ctf_router,
    projects_router,
    writeups_router,
    contact_router,
    attachments_router,
    portfolio_router,
    admin_router,
)
# Importar Base de persistence donde están definidos los modelos
from .infrastructure.persistence.base import Base
from .infrastructure.persistence.models import (
    UserModel,
    ProjectModel,
    CTFModel,
    WriteupModel,
    AttachmentModel,
    ContactModel,
    FlagSubmissionModel,
    PortfolioProfileModel,
)


UNHANDLED_ERROR_DETAIL = "No fue posible completar la operación. Intenta nuevamente."


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para la aplicación."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # create_all solo en desarrollo; producción usa migraciones Alembic
    if settings.DEBUG:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Crear instancia de FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Portfolio Backend API
    
    Backend para portafolio personal con funcionalidades de:
    
    * **Autenticación** - Registro, login, JWT tokens
    * **Proyectos** - CRUD de proyectos del portafolio
    * **CTFs** - Gestión de retos Capture The Flag
    * **Writeups** - Documentación de soluciones CTF
    
    ### Arquitectura
    
    Clean Architecture + Hexagonal (Ports & Adapters)
    
    - **Domain**: Entidades, repositorios (interfaces), servicios de dominio
    - **Application**: Casos de uso, DTOs
    - **Infrastructure**: Implementaciones SQL, storage, JWT
    - **API**: Routers FastAPI
    """,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de seguridad (headers HTTP)
app.middleware("http")(security_headers_middleware)

# CSRF: Angular interceptor envía el header X-CSRF-Token
app.middleware("http")(csrf_protect_middleware)

# Configurar rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Errores no controlados: 500 genérico, traceback solo en logs."""
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if isinstance(exc, RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})
    if isinstance(exc, RateLimitExceeded):
        return rate_limit_exceeded_handler(request, exc)

    logger.error(
        "Unhandled exception on %s %s\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": UNHANDLED_ERROR_DETAIL},
    )


# Montar archivos estáticos (uploads)
# app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files")

# Registrar routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(ctf_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(writeups_router, prefix=settings.API_V1_PREFIX)
app.include_router(contact_router, prefix=settings.API_V1_PREFIX)
app.include_router(attachments_router, prefix=settings.API_V1_PREFIX)
app.include_router(portfolio_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz."""
    payload = {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
    if settings.DEBUG:
        payload["docs"] = "/docs"
        payload["redoc"] = "/redoc"
    return payload


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check: ping de base de datos (SELECT 1)."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "db": "ok"}
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "db": "error"},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
