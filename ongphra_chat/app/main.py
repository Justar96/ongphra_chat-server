import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import json

from app.routers.fortune import router as fortune_router
from app.routers.chat_router import router as chat_router
from app.config.settings import get_settings
from app.config.database import engine, Base, get_db
from app.models.database import ChatSession, ChatMessage  # Import models to ensure they're registered
from app.services.chat_service import ChatService
from app.utils.openai_client import OpenAIClient, get_openai_client
from app.utils.tool_handler import tool_handler

# Get application settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Add any startup code here (DB connections, etc.)
    logger.info("Starting up Thai Fortune API service...")
    
    # Create database tables if they don't exist
    logger.info("Connecting to MariaDB database...")
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
    
    yield
    
    # Shutdown: Add any cleanup code here
    logger.info("Shutting down Thai Fortune API service...")

app = FastAPI(
    title="Thai Fortune API",
    description="API for Thai fortune telling with OpenAI integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred"},
        )

# Include routers
app.include_router(fortune_router, prefix="/api/v1", tags=["fortune"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])

# Dependencies
def get_chat_service(db=Depends(get_db)):
    return ChatService(db)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Thai Fortune API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)