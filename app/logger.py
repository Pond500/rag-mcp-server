"""
Centralized Logging Configuration
Provides rotating file logs with detailed DEBUG info and clean console INFO output
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name: str = "mcp_server", log_level: int = logging.DEBUG) -> logging.Logger:
    """
    Setup centralized logger with file rotation and console output
    
    Args:
        name: Logger name (default: "mcp_server")
        log_level: Root log level (default: DEBUG)
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "server.log"
    
    # ========================================
    # Console Handler (INFO level, simple format)
    # ========================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        fmt='%(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # ========================================
    # File Handler (DEBUG level, detailed format with rotation)
    # ========================================
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # ========================================
    # Silence noisy libraries
    # ========================================
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    
    logger.info(f"✅ Logger initialized: {name}")
    logger.debug(f"Log file: {log_file.absolute()}")
    
    return logger


# Global logger instance
logger = setup_logger()
