# app/main.py
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uvicorn

from app.api.router import router as fortune_router
from app.core.exceptions import FortuneServiceException
from app.config.settings import get_settings

# Get settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Thai Fortune Teller API",
    description="API for Thai 7 Numbers 9 Bases fortune telling",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add router
app.include_router(fortune_router)


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
@app.exception_handler(FortuneServiceException)
async def fortune_exception_handler(request: Request, exc: FortuneServiceException):
    """Handle FortuneServiceException with appropriate error message"""
    logger.error(f"FortuneServiceException: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


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


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Thai Fortune Teller API",
        "version": "1.0.0",
        "description": "Traditional Thai 7 Numbers 9 Bases fortune telling system",
        "endpoints": {
            "fortune": "/fortune - Get a fortune reading",
            "system_info": "/fortune/system-info - Get system information"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    """Run the application directly"""
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.debug
    )