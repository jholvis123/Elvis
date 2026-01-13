"""
Configuración centralizada de logging.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from .config import settings


class JSONFormatter(logging.Formatter):
    """Formateador JSON para logs estructurados (ideal para producción)."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Añadir información de excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Añadir campos extra si existen
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Formateador con colores para desarrollo."""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# Formato de logs para desarrollo
DEV_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


def setup_logging() -> logging.Logger:
    """Configura y retorna el logger principal."""
    
    # Nivel basado en modo debug
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Crear handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Usar formateador apropiado según el entorno
    if settings.DEBUG:
        # Desarrollo: formato legible con colores
        formatter = ColoredFormatter(DEV_LOG_FORMAT)
    else:
        # Producción: JSON estructurado
        formatter = JSONFormatter()
    
    handler.setFormatter(formatter)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]
    
    # Logger específico de la app
    logger = logging.getLogger(settings.APP_NAME)
    logger.setLevel(level)
    
    # Reducir verbosidad de librerías externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con nombre específico.
    
    Args:
        name: Nombre del logger (usualmente __name__).
        
    Returns:
        Logger configurado.
    """
    return logging.getLogger(f"{settings.APP_NAME}.{name}")


# Logger principal de la aplicación
logger = setup_logging()
