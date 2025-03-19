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

# Check if this is a worker process
is_parent_process = os.environ.get("IS_PARENT_PROCESS", "true").lower() == "true"
worker_id = os.getenv("WORKER_ID", "0")

def setup_logging():
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    Path(LOG_DIR).mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Set lower log level for worker processes to reduce noise
    if is_parent_process:
        root_logger.setLevel(LOG_LEVEL)
    else:
        # Use INFO or DEBUG depending on the configured level
        if LOG_LEVEL == "DEBUG":
            root_logger.setLevel(logging.DEBUG)
        else:
            # Workers use higher level threshold to reduce noise
            root_logger.setLevel(logging.WARNING)
    
    # Clear any existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(LOG_FORMAT if is_parent_process else 
                                         f"[Worker-{worker_id}] - {LOG_FORMAT}")
    console_handler.setFormatter(console_formatter)
    
    # Force UTF-8 encoding for console output
    try:
        # This might not work on all platforms, so we wrap it in a try-except
        import codecs
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ImportError):
        # For older Python versions or platforms that don't support reconfigure
        if hasattr(sys.stdout, 'encoding'):
            sys.stdout.encoding = 'utf-8'
    
    root_logger.addHandler(console_handler)
    
    # File handler with rotation and UTF-8 encoding - only add in parent process
    # or with reduced logging level in workers
    file_handler = SafeRotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE),
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'  # Use UTF-8 encoding for log files
    )
    
    # Use different log format for workers
    file_formatter = logging.Formatter(LOG_FORMAT if is_parent_process else
                                      f"[Worker-{worker_id}] - {LOG_FORMAT}")
    file_handler.setFormatter(file_formatter)
    
    # Set different logging levels for workers to reduce noise
    if not is_parent_process:
        file_handler.setLevel(logging.WARNING)
    
    root_logger.addHandler(file_handler)
    
    # Set log levels for specific libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.ERROR)  # Disable watchfiles debug logs
    
    # Log setup complete
    if is_parent_process:
        root_logger.debug("Logging setup complete")

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    logger = logging.getLogger(name)
    
    # Set different level for repository loggers in worker processes
    if not is_parent_process and (name.startswith("app.repository") or 
                                 name.startswith("app.services")):
        logger.setLevel(logging.WARNING)
    
    return logger

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
    elif not is_parent_process:
        # For worker processes, use higher threshold
        if name.startswith("app.repository") or name.startswith("app.services"):
            logger.setLevel(logging.WARNING)
    
    return logger 