#!/usr/bin/env python
# start_server.py - Production server launcher with optimized settings
import os
import logging
import uvicorn
import sys
from pathlib import Path

def setup_environment():
    """Configure environment variables for production"""
    # Set log level to INFO if not explicitly set to something else
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    # Disable debug mode for production
    os.environ["DEBUG"] = "false"
    
    # Disable watchfiles auto-reload in production
    os.environ["WATCHFILES_FORCE_POLLING"] = "false"

def configure_logging():
    """Configure logging specifically for the server launcher"""
    # Disable debug logging for noisy modules
    logging.getLogger("watchfiles").setLevel(logging.ERROR)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

def start_server():
    """Start the FastAPI server with production settings"""
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
        
        print(f"Starting server on {host}:{port} in production mode...")
        
        # Start uvicorn with optimized settings for production
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=False,  # Disable auto-reload in production
            workers=4,     # Use multiple workers for better performance
            log_level=os.environ.get("LOG_LEVEL", "info").lower(),
            access_log=False  # Disable access logs to reduce noise
        )
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    start_server() 