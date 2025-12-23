"""
Portfolio Backend - Clean Architecture + Hexagonal

Punto de entrada principal de la aplicación FastAPI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.database import engine
from .core.logging import logger
from .core.security_middleware import (
    limiter, 
    security_headers_middleware,
    rate_limit_exceeded_handler
)
from .api.routers import (
    auth_router,
    ctf_router,
    projects_router,
    writeups_router,
    contact_router,
    attachments_router,
    portfolio_router,
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
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para la aplicación."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Crear tablas de la base de datos
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
    docs_url="/docs",
    redoc_url="/redoc",
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

# Configurar rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

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


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
