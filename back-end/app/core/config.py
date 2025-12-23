"""
Configuración central de la aplicación.
Usa Pydantic Settings para manejar variables de entorno.
"""

from functools import lru_cache
from typing import List
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
    
    # Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".md", ".pdf", ".png", ".jpg", ".pcap"]
    
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
