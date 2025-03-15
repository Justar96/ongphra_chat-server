# app/api/router.py
from datetime import datetime
from typing import Dict, Optional, Any, List, AsyncGenerator

import uuid
from fastapi import APIRouter, HTTPException, Depends, Query, Cookie, Response, Request
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from app.core.service import FortuneService
from app.core.exceptions import FortuneServiceException
from app.services.calculator import CalculatorService
from app.services.meaning import MeaningService 
from app.services.prompt import PromptService
from app.services.response import ResponseService
from app.services.reading_service import ReadingService, get_reading_service
from app.repository.category_repository import CategoryRepository
from app.repository.reading_repository import ReadingRepository
from app.domain.birth import BirthInfo
from app.domain.meaning import Category, Reading, MeaningCollection
from app.config.settings import get_settings


# Pydantic models for API
class FortuneRequest(BaseModel):
    birth_date: Optional[str] = Field(None, description="Format: YYYY-MM-DD")
    thai_day: Optional[str] = Field(None, description="Thai day name")
    question: str = Field(..., description="The question to ask the fortune teller")
    language: str = Field("thai", description="Response language (thai or english)")
    stream: bool = Field(False, description="Whether to stream the response")


class FortuneResponse(BaseModel):
    fortune: str
    bases: Optional[Dict[str, Any]] = None
    birth_info: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class UserSession(BaseModel):
    session_id: str
    birth_date: Optional[str] = None
    thai_day: Optional[str] = None
    language: str
    last_interaction: datetime


# Create router
router = APIRouter(prefix="/fortune", tags=["fortune"])


# Dependency to get FortuneService
def get_fortune_service() -> FortuneService:
    """Dependency for getting the FortuneService instance"""
    settings = get_settings()
    
    # Initialize repositories
    category_repository = CategoryRepository(
        settings.categories_path, Category
    )
    reading_repository = ReadingRepository(
        settings.readings_path, Reading
    )
    
    # Initialize services
    calculator_service = CalculatorService()
    meaning_service = MeaningService(
        category_repository, reading_repository
    )
    prompt_service = PromptService()
    response_service = ResponseService()
    
    # Create and return FortuneService
    return FortuneService(
        calculator_service,
        meaning_service,
        prompt_service,
        response_service
    )


# Get or create a session ID
async def get_session_id(
    request: Request,
    session_id: Optional[str] = Cookie(None),
    fortune_service: FortuneService = Depends(get_fortune_service)
) -> str:
    """Get or create a session ID for the user"""
    if session_id and await fortune_service.get_user_session_info(session_id):
        return session_id
    
    # Generate a new session ID
    new_session_id = str(uuid.uuid4())
    return new_session_id


async def fortune_generator(generator):
    """Convert AsyncGenerator to sync generator for StreamingResponse"""
    async for chunk in generator:
        yield chunk


@router.post("", response_model=FortuneResponse)
async def get_fortune(
    request: FortuneRequest,
    response: Response,
    fortune_service: FortuneService = Depends(get_fortune_service),
    session_id: Optional[str] = Cookie(None)
) -> Dict[str, Any]:
    """
    Get fortune telling response based on birth date and question
    
    If birth_date and thai_day are provided, will give a personalized reading.
    If not provided, will give a general response and guidance.
    """
    try:
        # Generate or use existing session ID
        if not session_id:
            session_id = str(uuid.uuid4())
            response.set_cookie(key="session_id", value=session_id)
        
        # Check if birth information is provided
        if request.birth_date and request.thai_day:
            # Parse the birth date
            try:
                birth_date = datetime.strptime(request.birth_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid birth date format. Use YYYY-MM-DD."
                )
            
            # Get complete fortune with birth info
            result = await fortune_service.get_fortune(
                birth_date=birth_date,
                thai_day=request.thai_day,
                question=request.question,
                language=request.language,
                user_id=session_id
            )
            
            # Return full response
            return {
                "fortune": result.fortune,
                "bases": result.bases.to_dict() if result.bases else None,
                "birth_info": result.birth_info.to_dict() if result.birth_info else None,
                "session_id": session_id
            }
        else:
            # Get general response without birth info
            general_response = await fortune_service.get_general_response(
                question=request.question,
                language=request.language,
                user_id=session_id
            )
            
            # Return limited response without bases or birth info
            return {
                "fortune": general_response,
                "bases": None,
                "birth_info": None,
                "session_id": session_id
            }
            
    except FortuneServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/session", response_model=Dict[str, Any])
async def get_session_info(
    session_id: str = Cookie(...),
    fortune_service: FortuneService = Depends(get_fortune_service)
) -> Dict[str, Any]:
    """Get information about the current session"""
    session_info = await fortune_service.get_user_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "session_info": session_info
    }


@router.get("/system-info", response_model=Dict[str, str])
async def get_system_info() -> Dict[str, str]:
    """Get information about the fortune telling system"""
    return {
        "name": "Thai 7 Numbers 9 Bases Fortune Telling",
        "description": "Traditional Thai divination system based on birth date",
        "version": "1.0.0",
    }


@router.post("/meanings", response_model=Dict[str, Any])
async def extract_meanings(
    request: FortuneRequest,
    reading_service: ReadingService = Depends(get_reading_service),
    fortune_service: FortuneService = Depends(get_fortune_service)
) -> Dict[str, Any]:
    """
    Extract meanings from calculator results based on birth information
    """
    try:
        # Parse birth date
        if not request.birth_date or not request.thai_day:
            raise HTTPException(status_code=400, detail="Birth date and Thai day are required")
            
        birth_date = datetime.strptime(request.birth_date, "%Y-%m-%d")
        
        # Calculate bases
        calculator = CalculatorService()
        bases_result = calculator.calculate_birth_bases(birth_date, request.thai_day)
        
        # Extract meanings
        meanings = await reading_service.extract_meanings_from_calculator_result(bases_result)
        
        # Return response
        return {
            "birth_info": bases_result.birth_info.model_dump(),
            "bases": bases_result.bases.model_dump(),
            "meanings": meanings.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting meanings: {str(e)}")