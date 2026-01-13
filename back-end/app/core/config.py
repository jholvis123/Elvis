"""
Configuración central de la aplicación.
Usa Pydantic Settings para manejar variables de entorno.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""
    
    # App
    APP_NAME: str = "Portfolio Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:4200"]
    
    # Database - MySQL via XAMPP
    DATABASE_URL: str = "mysql+pymysql://root:@localhost:3306/portfolio_db"
    
    # JWT
    SECRET_KEY: str  # Must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Cookie Security Settings
    COOKIE_SECURE: bool = False  # True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"  # "strict" for highest security, "lax" for usability
    COOKIE_DOMAIN: Optional[str] = None  # Set in production
    
    # CSRF Protection
    CSRF_SECRET_KEY: Optional[str] = None  # Will default to SECRET_KEY if not set
    
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
