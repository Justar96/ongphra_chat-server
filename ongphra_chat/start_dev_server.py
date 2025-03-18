#!/usr/bin/env python
# start_dev_server.py - Development server launcher with optimized watchfiles configuration
import os
import logging
import uvicorn
import sys
from pathlib import Path

def setup_environment():
    """Configure environment variables for development"""
    # Set log level
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    
    # Enable debug mode for development
    os.environ["DEBUG"] = "true"
    
    # Configure watchfiles to reduce logging noise
    os.environ["WATCHFILES_FORCE_POLLING"] = "false"

def configure_logging():
    """Configure logging to reduce noise from watchfiles"""
    # Disable debug logging for watchfiles even in development
    logging.getLogger("watchfiles").setLevel(logging.ERROR)
    
    # Keep other modules at debug level for development
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.DEBUG)

def start_dev_server():
    """Start the FastAPI server with development settings but optimized logging"""
    try:
        # Ensure cwd is the project root
        project_root = Path(__file__).resolve().parent
        os.chdir(project_root)
        
        # Configure environment and logging
        setup_environment()
        configure_logging()
        
        # Get host and port from environment or use defaults
        host = os.environ.get("HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", "8000"))
        
        print(f"Starting development server on {host}:{port}...")
        print(f"API documentation available at http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
        
        # Start uvicorn with development settings
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=True,             # Enable auto-reload for development
            reload_delay=1,          # Reduce the delay between reload checks
            workers=1,               # Use a single worker for development
            log_level=os.environ.get("LOG_LEVEL", "debug").lower()
        )
    except Exception as e:
        print(f"Error starting development server: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    start_dev_server() 