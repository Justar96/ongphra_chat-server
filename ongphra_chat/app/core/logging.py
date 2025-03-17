# app/core/logging.py
import logging
import os
import sys
import stat
from logging.handlers import RotatingFileHandler
from typing import Optional
from pathlib import Path

class SafeRotatingFileHandler(RotatingFileHandler):
    """
    A RotatingFileHandler subclass that handles file permission issues more gracefully.
    This implementation ensures proper file permissions and handles rotation errors.
    """
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=True):
        """Initialize with delay=True by default to prevent file access issues at startup"""
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay=True)
        
    def _open(self):
        """
        Open the log file with proper permissions, ensuring it's writable
        """
        # Open the file with standard handler
        stream = super()._open()
        
        # Set appropriate permissions on Windows
        try:
            # Make sure the file is readable and writable by the current user
            os.chmod(self.baseFilename, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            # If we can't set permissions, just continue - we've already logged to console as fallback
            pass
            
        return stream
    
    def doRollover(self):
        """
        Override doRollover to handle permission errors during rotation
        """
        try:
            # Try standard rotation
            super().doRollover()
        except (PermissionError, OSError) as e:
            # If rotation fails, log to stderr and continue with the current file
            sys.stderr.write(f"Failed to rotate log file {self.baseFilename}: {str(e)}\n")
            # Try to continue with the current file
            self.mode = 'a'  # Append mode
            try:
                # Try to reopen the current file
                if self.encoding:
                    self.stream = open(self.baseFilename, self.mode, encoding=self.encoding)
                else:
                    self.stream = open(self.baseFilename, self.mode)
            except Exception as e2:
                # If reopening fails, we have no choice but to disable file logging
                sys.stderr.write(f"Failed to reopen log file {self.baseFilename}: {str(e2)}\n")
                self.stream = None

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = "logs"
LOG_FILE = "app.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

def setup_logging():
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    Path(LOG_DIR).mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    
    # Clear any existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE),
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(file_handler)
    
    # Set log levels for specific libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    # Log setup complete
    root_logger.debug("Logging setup complete")

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def get_logger_with_level(name: str, level: Optional[str] = None) -> logging.Logger:
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
        try:
            # Create logs directory if it doesn't exist
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Create a file handler for CSV operations
            csv_log_file = os.path.join(logs_dir, "csv_operations.log")
            file_handler = SafeRotatingFileHandler(
                csv_log_file, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'  # Ensure UTF-8 encoding
            )
            
            # Set formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(file_handler)
            
            # Add console handler as fallback
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
        except Exception as e:
            # If file handler setup fails, use console logging as fallback
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # Log the error to console
            logger.warning(f"Failed to set up file logging: {str(e)}. Using console logging instead.")
    
    return logger 