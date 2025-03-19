# app/main.py
from openai import AsyncOpenAI
from fastapi import FastAPI, Request, Response, Depends, Query, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import os
import sys
import uvicorn
from datetime import datetime
from typing import Optional

from app.config.settings import get_settings
from app.config.database import DatabaseManager
from app.repository.category_repository import CategoryRepository
from app.repository.reading_repository import ReadingRepository
from app.repository.chat_repository import ChatRepository
from app.services.reading_service import ReadingService, get_reading_service
from app.services.chat_service import ChatService, get_chat_service
from app.domain.meaning import Category, Reading
from app.core.logging import setup_logging, get_logger
from app.routers.api_router import router as api_router
from app.routers.ai_tools_router import router as ai_tools_router
from app.routers.chat_router import router as chat_router

"""
Ongphra Chat API - Main Application

This application provides fortune telling and AI chat capabilities with the following endpoints:

1. `/api/chat` - Main chat endpoint that supports both regular conversation and fortune readings
   - Uses AI with memory to maintain context across conversations
   - Automatically detects and processes fortune reading requests when enabled
   - Parameters include: prompt, birth_date (optional), thai_day (optional), enable_fortune (default: true)

2. `/api/chat/stream` - Streaming version of the chat endpoint
   - Same functionality as the regular chat endpoint, but streams responses
   - Better user experience for long responses

3. `/api/fortune` - Direct endpoint for fortune readings
   - Requires birth date to be provided
   - Uses the same underlying fortune processing system as the chat endpoints
   - Simplified interface when only fortune readings are needed

4. `/api/birth-chart/enriched` - Detailed birth chart information
   - Advanced endpoint for getting detailed astrological information
   - Returns full birth chart with meanings

5. `/api/ai-tools/*` - AI tool endpoints for advanced usage
   - Direct access to AI tools for specialized applications

The system integrates session management, fortune calculation, and dynamic prompt generation
for a comprehensive fortune telling experience.
"""

# Determine if this is the main/parent process or a worker
is_parent_process = os.environ.get("IS_PARENT_PROCESS", "true").lower() == "true"
worker_id = os.getenv("WORKER_ID", "0")

# Setup logging only once in the parent process
if is_parent_process:
    # Initialize logging
    setup_logging()
    
# Get a logger for this module
logger = get_logger(__name__)

# Initialize settings
settings = get_settings()

# Ensure logs directory exists - only in parent process to avoid race conditions
if is_parent_process:
    logs_dir = os.path.join(settings.base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    logger.debug("Logs directory created/verified")

# Configure meaning service logger
meaning_logger = logging.getLogger('app.services.meaning')
if not meaning_logger.handlers:
    meaning_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

# Log startup information - only in parent process or with lower verbosity in workers
if is_parent_process:
    logger.info("Application starting up (parent process)")
else:
    logger.info(f"Worker {worker_id} starting up")

# Try to import WeasyPrint for PDF generation
_has_weasyprint = None
def has_weasyprint():
    global _has_weasyprint
    if _has_weasyprint is None:
        try:
            from weasyprint import HTML
            _has_weasyprint = True
            if is_parent_process:
                logger.info("WeasyPrint successfully imported for PDF generation")
            else:
                logger.debug("WeasyPrint imported in worker process")
        except ImportError:
            _has_weasyprint = False
            if is_parent_process:
                logger.warning("WeasyPrint not available. PDF export functionality will be disabled.")
            else:
                logger.debug("WeasyPrint not available in worker process")
        except Exception as e:
            _has_weasyprint = False
            if is_parent_process:
                logger.warning(f"Error importing WeasyPrint: {str(e)}. PDF export functionality will be disabled.")
            else:
                logger.debug(f"Error importing WeasyPrint in worker process: {str(e)}")
    
    return _has_weasyprint

# Singleton app instance
_app_instance = None

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    global _app_instance
    
    # Return existing instance if already created
    if _app_instance is not None:
        return _app_instance
    
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
    
    # Add API router
    app.include_router(api_router)
    app.include_router(ai_tools_router)  # Add the AI tools router
    app.include_router(chat_router)      # Add the chat history router
    
    # Log with different verbosity based on process type
    if is_parent_process:
        logger.info("Application initialized")
    else:
        logger.info(f"Worker {worker_id} application initialized")
    
    # Store as singleton
    _app_instance = app
    return app

app = create_application()

# Track if database has been initialized
_db_initialized = False

# Store service and repository instances
_services = {}
_repositories = {}

# Register repositories and services for dependency injection
@app.on_event("startup")
async def startup_event():
    global _db_initialized, _services, _repositories
    
    # Initialize database connection pool if not already initialized
    if not _db_initialized:
        if is_parent_process:
            logger.info("Initializing database connection pool")
        else:
            logger.info(f"Worker {worker_id} initializing database connection pool")
            
        await DatabaseManager.initialize_pool()
        _db_initialized = True
    
    # Create repositories if not already created
    if not _repositories:
        _repositories["category_repository"] = CategoryRepository()
        _repositories["reading_repository"] = ReadingRepository()
        _repositories["chat_repository"] = ChatRepository()
        
        if is_parent_process:
            logger.info("Repositories initialized")
        else:
            logger.info(f"Worker {worker_id} repositories initialized")
    
    # Create services if not already created
    if not _services:
        # Initialize reading service with actual repository instances
        _services["reading_service"] = ReadingService(
            reading_repository=_repositories["reading_repository"],
            category_repository=_repositories["category_repository"]
        )
        
        # Initialize chat service
        _services["chat_service"] = ChatService(
            chat_repository=_repositories["chat_repository"]
        )
        
        if is_parent_process:
            logger.info("Services initialized")
        else:
            logger.info(f"Worker {worker_id} services initialized")

# Shutdown event to close database connections
@app.on_event("shutdown")
async def shutdown_event():
    if is_parent_process:
        logger.info("Shutting down application")
    else:
        logger.info(f"Worker {worker_id} shutting down")
        
    await DatabaseManager.close_pool()
    
    if is_parent_process:
        logger.info("Database connections closed")
    else:
        logger.info(f"Worker {worker_id} database connections closed")

# Register dependency injection functions
def get_category_repository():
    return _repositories["category_repository"]

def get_reading_repository():
    return _repositories["reading_repository"]

def get_chat_repository():
    return _repositories["chat_repository"]

def get_reading_service_instance():
    return _services["reading_service"]

def get_chat_service_instance():
    return _services["chat_service"]

# Override the dependencies
app.dependency_overrides[CategoryRepository] = get_category_repository
app.dependency_overrides[ReadingRepository] = get_reading_repository
app.dependency_overrides[ChatRepository] = get_chat_repository
app.dependency_overrides[get_reading_service] = get_reading_service_instance
app.dependency_overrides[get_chat_service] = get_chat_service_instance

# Add middleware for request timing and logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # Log request - skip logging for health check endpoints to reduce noise
    path = request.url.path
    if path != "/health" and path != "/" and path != "/favicon.ico":
        if is_parent_process:
            logger.info(f"Request: {request.method} {path}")
        else:
            logger.info(f"Worker {worker_id} - Request: {request.method} {path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Worker-ID"] = worker_id
    
    # Log response - skip for health checks
    if path != "/health" and path != "/" and path != "/favicon.ico":
        if is_parent_process or process_time > 1.0:  # Only log slow responses in workers
            logger.info(f"Response: {response.status_code} - Process time: {process_time:.4f}s")
        else:
            logger.info(f"Worker {worker_id} - Response: {response.status_code} - Process time: {process_time:.4f}s")
    
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
        "docs_url": "/docs",
        "worker_id": worker_id
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "worker_id": worker_id
    }


if __name__ == "__main__":
    # Check if WeasyPrint is available
    has_weasyprint()
    
    # Run the app directly if executed as a script
    uvicorn.run(app, host="0.0.0.0", port=8000)