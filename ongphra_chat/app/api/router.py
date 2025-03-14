# app/api/router.py
from datetime import datetime
from typing import Dict, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.core.service import FortuneService
from app.core.exceptions import FortuneServiceException
from app.services.calculator import CalculatorService
from app.services.meaning import MeaningService 
from app.services.prompt import PromptService
from app.services.response import ResponseService
from app.repository.category_repository import CategoryRepository
from app.repository.reading_repository import ReadingRepository
from app.domain.birth import BirthInfo
from app.domain.meaning import Category, Reading
from app.config.settings import get_settings


# Pydantic models for API
class FortuneRequest(BaseModel):
    birth_date: Optional[str] = Field(None, description="Format: YYYY-MM-DD")
    thai_day: Optional[str] = Field(None, description="Thai day name")
    question: str = Field(..., description="The question to ask the fortune teller")
    language: str = Field("thai", description="Response language (thai or english)")


class FortuneResponse(BaseModel):
    fortune: str
    bases: Optional[Dict[str, Any]] = None
    birth_info: Optional[Dict[str, Any]] = None


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


@router.post("", response_model=FortuneResponse)
async def get_fortune(
    request: FortuneRequest,
    fortune_service: FortuneService = Depends(get_fortune_service)
) -> Dict[str, Any]:
    """
    Get fortune telling response based on birth date and question
    
    If birth_date and thai_day are provided, will give a personalized reading.
    If not provided, will give a general response and guidance.
    """
    try:
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
                language=request.language
            )
            
            # Return full response
            return {
                "fortune": result.fortune,
                "bases": result.bases.to_dict() if result.bases else None,
                "birth_info": result.birth_info.to_dict() if result.birth_info else None
            }
        else:
            # Get general response without birth info
            general_response = await fortune_service.get_general_response(
                question=request.question,
                language=request.language
            )
            
            # Return limited response without bases or birth info
            return {
                "fortune": general_response,
                "bases": None,
                "birth_info": None
            }
            
    except FortuneServiceException as e:
        # Handle specific service exceptions
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/system-info", response_model=Dict[str, str])
async def get_system_info() -> Dict[str, str]:
    """Get information about the fortune telling system"""
    return {
        "name": "Thai 7 Numbers 9 Bases Fortune Telling",
        "description": "Traditional Thai divination system based on birth date",
        "version": "1.0.0",
    }