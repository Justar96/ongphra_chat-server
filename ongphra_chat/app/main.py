# app/main.py
import logging
import os
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request, Response, Form, Depends, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import time
import uvicorn
from datetime import datetime
from typing import Optional
import tempfile
import importlib.util

from ongphra_chat.app.config.settings import get_settings
from ongphra_chat.app.config.database import DatabaseManager
from ongphra_chat.app.repository.category_repository import CategoryRepository
from ongphra_chat.app.repository.reading_repository import ReadingRepository
from ongphra_chat.app.services.reading_service import ReadingService, get_reading_service
from ongphra_chat.app.domain.meaning import Category, Reading
from ongphra_chat.app.core.logging import setup_logging, get_logger
from ongphra_chat.app.routers.api_router import router as api_router

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize settings
settings = get_settings()

# Ensure logs directory exists
logs_dir = os.path.join(settings.base_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)

# Ensure static directory exists
static_dir = os.path.join(settings.base_dir, "static")
os.makedirs(static_dir, exist_ok=True)

# Configure logging
log_file = os.path.join(logs_dir, "app.log")
csv_log_file = os.path.join(logs_dir, "csv_operations.log")

# Configure root logger with error handling
try:
    from app.core.logging import SafeRotatingFileHandler
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console handler
            SafeRotatingFileHandler(
                log_file, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8',  # Ensure UTF-8 encoding for Thai characters
                delay=True  # Delay file opening until first log record is emitted
            )
        ]
    )
except Exception as e:
    # Fallback to console-only logging if file logging fails
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]  # Console handler only
    )
    logging.warning(f"Failed to set up file logging: {str(e)}. Using console logging only.")

# Configure CSV operations logger with error handling
try:
    from app.core.logging import SafeRotatingFileHandler
    
    csv_logger = logging.getLogger('app.repository')
    csv_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    csv_handler = SafeRotatingFileHandler(
        csv_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8',  # Ensure UTF-8 encoding for Thai characters
        delay=True  # Delay file opening until first log record is emitted
    )
    csv_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    csv_logger.addHandler(csv_handler)
except Exception as e:
    # If CSV file handler setup fails, ensure we have console logging
    csv_logger = logging.getLogger('app.repository')
    if not any(isinstance(h, logging.StreamHandler) for h in csv_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        csv_logger.addHandler(console_handler)
    logging.warning(f"Failed to set up CSV file logging: {str(e)}. Using console logging for repository operations.")

# Configure meaning service logger
meaning_logger = logging.getLogger('app.services.meaning')
meaning_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

# Get main logger
logger = logging.getLogger(__name__)
logger.info("Application starting up with logging configured")
logger.info(f"CSV operations will be logged to: {csv_log_file}")
logger.info(f"General logs will be written to: {log_file}")

# Try to import WeasyPrint for PDF generation
try:
    from weasyprint import HTML
    has_weasyprint = True
    logger.info("WeasyPrint successfully imported for PDF generation")
except ImportError:
    has_weasyprint = False
    logger.warning("WeasyPrint not available. PDF export functionality will be disabled.")
except Exception as e:
    has_weasyprint = False
    logger.warning(f"Error importing WeasyPrint: {str(e)}. PDF export functionality will be disabled.")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Ongphra Chat API",
        description="API for fortune telling and chat with context memory",
        version="1.0.0"
    )
    
    # Configure CORS
    origins = settings.cors_origins
    if isinstance(origins, str):
        if origins == "*":
            origins = ["*"]
        else:
            origins = [origin.strip() for origin in origins.split(",")]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Add API router
    app.include_router(api_router)
    
    logger.info("Application initialized")
    return app

app = create_application()

# Register repositories and services for dependency injection
@app.on_event("startup")
async def startup_event():
    # Initialize database connection pool
    logger.info("Initializing database connection pool")
    await DatabaseManager.initialize_pool()
    
    # Initialize repositories
    app.state.category_repository = CategoryRepository()
    app.state.reading_repository = ReadingRepository()
    
    # Initialize services
    app.state.reading_service = ReadingService(
        app.state.reading_repository,
        app.state.category_repository
    )
    
    logging.info("Repositories and services initialized")

# Shutdown event to close database connections
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")
    await DatabaseManager.close_pool()
    logger.info("Database connections closed")

# Register dependencies
def get_category_repository():
    return app.state.category_repository

def get_reading_repository():
    return app.state.reading_repository

def get_reading_service_instance():
    return app.state.reading_service

app.dependency_overrides[CategoryRepository] = get_category_repository
app.dependency_overrides[ReadingRepository] = get_reading_repository
app.dependency_overrides[get_reading_service] = get_reading_service_instance

# Add middleware for request timing and logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log response
    logger.info(f"Response: {response.status_code} - Process time: {process_time:.4f}s")
    
    return response


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with a generic error message"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # In production, don't expose the actual error
    if settings.debug:
        detail = str(exc)
    else:
        detail = "An internal server error occurred"
    
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Ongphra Chat API",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # Run the application with uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )