# app/core/logging.py
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name and level
    
    Args:
        name: Logger name (usually __name__ of the module)
        level: Optional logging level to override the default
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level if provided
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    
    # Configure CSV operations logger if it's a repository module
    if "repository" in name and not logger.handlers:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create a file handler for CSV operations
        csv_log_file = os.path.join(logs_dir, "csv_operations.log")
        file_handler = RotatingFileHandler(
            csv_log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        # Set formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
    return logger 