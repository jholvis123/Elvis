"""
Configuración centralizada de logging.
"""

import logging
import sys
from .config import settings

# Formato de logs
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging() -> logging.Logger:
    """Configura y retorna el logger principal."""
    
    # Nivel basado en modo debug
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Configurar logger raíz
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Logger específico de la app
    logger = logging.getLogger(settings.APP_NAME)
    logger.setLevel(level)
    
    return logger


logger = setup_logging()
