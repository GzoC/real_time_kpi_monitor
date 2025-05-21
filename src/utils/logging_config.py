"""
logging_config.py
Configuración centralizada de logging para todo el proyecto.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(
    logger_name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configura un logger con un formato consistente y rotación de archivos.
    
    Args:
        logger_name: Nombre del logger
        log_file: Ruta al archivo de log (opcional)
        level: Nivel de logging
        max_bytes: Tamaño máximo del archivo de log antes de rotar
        backup_count: Número de archivos de backup a mantener
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Formato consistente para todos los logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo si se especifica
    if log_file:
        # Crear directorio de logs si no existe
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado.
    
    Args:
        name: Nombre del módulo (usar __name__)
    
    Returns:
        Logger configurado
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    log_file = os.path.join(log_dir, f'{name}.log')
    
    return setup_logger(name, log_file)
