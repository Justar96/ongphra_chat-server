#!/usr/bin/env python
# start_server.py - Production server launcher with optimized settings
import os
import logging
import uvicorn
import sys
import multiprocessing
from pathlib import Path

def setup_environment():
    """Configure environment variables for production"""
    # Set log level to INFO if not explicitly set to something else
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    # Disable debug mode for production
    os.environ["DEBUG"] = "false"
    
    # Disable watchfiles auto-reload in production
    os.environ["WATCHFILES_FORCE_POLLING"] = "false"
    
    # Add a flag to identify the main/parent process vs worker processes
    os.environ["IS_PARENT_PROCESS"] = "true"

def configure_logging():
    """Configure logging specifically for the server launcher"""
    # Disable debug logging for noisy modules
    logging.getLogger("watchfiles").setLevel(logging.ERROR)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

# Custom Uvicorn worker class to handle worker IDs
class WorkerConfig(uvicorn.Config):
    """Custom Uvicorn configuration with worker ID handling"""
    
    def __init__(self, *args, **kwargs):
        """Initialize with worker ID support"""
        super().__init__(*args, **kwargs)
        self._worker_id = 0
        
        # Ensure the IS_PARENT_PROCESS flag is set to true for the parent process
        os.environ["IS_PARENT_PROCESS"] = "true"
        
        # Initialize worker ID to 0 for the parent process
        os.environ["WORKER_ID"] = "0"
    
    @property
    def worker_id(self):
        """Return the current worker ID from process ID"""
        return getattr(self, "_worker_id", 0)
    
    @worker_id.setter
    def worker_id(self, value):
        """Set the worker ID and update environment variables"""
        self._worker_id = value
        # Set the worker ID in the environment
        os.environ["WORKER_ID"] = str(value)
        # Mark as not the parent process
        os.environ["IS_PARENT_PROCESS"] = "false"
        
        # Log worker startup with worker ID
        print(f"Starting worker {value}")

def start_server():
    """Start the FastAPI server with production settings"""
    try:
        # Ensure cwd is the project root
        project_root = Path(__file__).resolve().parent
        os.chdir(project_root)
        
        # Add the project root to the Python path
        sys.path.insert(0, str(project_root))
        
        # Configure environment and logging
        setup_environment()
        configure_logging()
        
        # Get host and port from environment or use defaults
        host = os.environ.get("HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", "8000"))
        
        # Determine number of workers based on CPU cores
        # Default to min(4, cpu_count + 1) which is a common best practice
        worker_count = min(4, multiprocessing.cpu_count() + 1)
        
        print(f"Starting API server on {host}:{port} in production mode with {worker_count} workers...")
        print(f"API documentation available at http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
        
        # Create custom config with worker ID support
        config = WorkerConfig(
            app="app.main:app",
            host=host,
            port=port,
            reload=False,     # Disable auto-reload in production
            workers=worker_count,
            log_level=os.environ.get("LOG_LEVEL", "info").lower(),
            access_log=False, # Disable access logs to reduce noise
            log_config=None   # Let our app configure logging instead of Uvicorn
        )
        
        # Create and start server with our custom config
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    start_server() 