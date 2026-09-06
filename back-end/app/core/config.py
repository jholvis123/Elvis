"""
Configuración central de la aplicación.
Usa Pydantic Settings para manejar variables de entorno.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""
    
    # App
    APP_NAME: str = "Portfolio Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS (explicit origins only; never "*") — Pages FE origin included for Render API
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "https://jholvis123.github.io",
    ]
    
    # Database — SQLAlchemy URL-driven:
    # Local MySQL: mysql+pymysql://user:pass@localhost:3306/portfolio_db
    # Render Postgres: postgresql+psycopg2://user:pass@host:5432/dbname (sslmode=require)
    # Also accepts postgres:// / postgresql:// (normalized to +psycopg2)
    DATABASE_URL: str = "mysql+pymysql://root:@localhost:3306/portfolio_db"
    
    # JWT
    SECRET_KEY: str  # Must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Cookie Security Settings
    # Render+Pages cross-origin admin is limited with SameSite=lax; do not force None until FE ready.
    COOKIE_SECURE: bool = False  # True on Render (HTTPS)
    COOKIE_SAMESITE: str = "lax"  # keep lax for same-origin Docker; optional "none" later (+ Secure)
    COOKIE_DOMAIN: Optional[str] = None  # usually leave unset (API host)
    
    # CSRF Protection
    CSRF_SECRET_KEY: Optional[str] = None  # Will default to SECRET_KEY if not set

    # Public self-registration (personal portfolio: keep false in production)
    # Admin bootstrap remains create_admin.py — this only gates POST /auth/register
    ALLOW_PUBLIC_REGISTER: bool = False
    
    # Storage
    STORAGE_TYPE: str = "local"  # local, s3
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 1024 * 1024 * 1024  # 1GB (para ISOs, VMs)
    ALLOWED_EXTENSIONS: List[str] = [
        ".md", ".pdf", ".png", ".jpg", ".jpeg", ".gif", 
        ".pcap", ".pcapng", 
        ".zip", ".tar", ".gz", ".7z", ".rar", 
        ".iso", ".ova", ".qcow2", 
        ".exe", ".bin", ".elf", ".apk", ".jar",
        ".py", ".c", ".cpp", ".js", ".html", ".css", ".txt"
    ]
    
    # S3 Storage (Optional)
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Render often injects postgres://; SQLAlchemy needs an explicit driver."""
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            return "postgresql+psycopg2://" + value[len("postgres://"):]
        if value.startswith("postgresql://") and "+psycopg" not in value.split("://", 1)[0]:
            return "postgresql+psycopg2://" + value[len("postgresql://"):]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Retorna instancia cacheada de la configuración."""
    return Settings()


settings = get_settings()
