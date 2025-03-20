# app/routers/ai_tools_router.py
from fastapi import APIRouter, Request, Depends, HTTPException, Header, Response
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import json
import logging
import asyncio

from app.core.logging import get_logger
from app.services.response import ResponseService  # Import ResponseService directly
from app.services.calculator import CalculatorService  # Fix import path
from app.services.reading_service import get_reading_service
from app.core.dependencies import get_user_id

# Define router
router = APIRouter(prefix="/ai-tools")
logger = get_logger(__name__)

# Request/Response models
class FortuneRequest(BaseModel):
    """Fortune reading request model."""
    message: str = Field(..., description="User message requesting fortune reading")
    user_id: Optional[str] = Field(None, description="User identifier for session tracking")

class FortuneResponse(BaseModel):
    """Fortune reading response model."""
    is_fortune_request: bool = Field(..., description="Whether the message is a fortune reading request")
    needs_birthdate: bool = Field(..., description="Whether birthdate is needed to process the request")
    fortune_reading: Optional[Dict[str, Any]] = Field(None, description="Fortune reading data if available")
    user_message: str = Field(..., description="Original user message")
    extracted_birthdate: Optional[str] = Field(None, description="Extracted birthdate from message")
    error: Optional[str] = Field(None, description="Error message if any")

@router.post("/fortune", response_model=FortuneResponse)
async def process_fortune_request(
    request: FortuneRequest,
    user_id: str = Depends(get_user_id)
) -> FortuneResponse:
    """
    Process a potential fortune reading request
    
    Args:
        request: Fortune request data
        user_id: User identifier from dependency
        
    Returns:
        FortuneResponse with processing results
    """
    try:
        logger.info(f"Processing fortune request: {request.message[:30]}...")
        
        # Use user_id from request if provided, otherwise from dependency
        user_identifier = request.user_id or user_id
        
        # Create an instance of ResponseService
        response_service = ResponseService()
        
        # Process the fortune request using the integrated method in ResponseService
        result = await response_service.process_fortune_request(
            prompt=request.message,
            user_id=user_identifier
        )
        
        return FortuneResponse(**result)
    
    except Exception as e:
        logger.error(f"Error processing fortune request: {str(e)}", exc_info=True)
        # Return error response
        return FortuneResponse(
            is_fortune_request=False,
            needs_birthdate=False,
            fortune_reading=None,
            user_message=request.message,
            extracted_birthdate=None,
            error=str(e)
        )

# Add more endpoints as needed

@router.post("/calculator")
async def calculator_tool(
    request: Dict[str, Any],
    user_id: str = Depends(get_user_id)
) -> Dict[str, Any]:
    """
    Calculate birth base number based on birth date
    
    Args:
        request: Calculator request data
        user_id: User identifier from dependency
        
    Returns:
        Dictionary with calculation results
    """
    try:
        logger.info(f"Processing calculator request with data: {json.dumps(request)}")
        
        # Extract birth date parameters
        birth_date_str = request.get("birth_date")
        if not birth_date_str:
            raise HTTPException(status_code=400, detail="Birth date is required")
        
        # Initialize calculator service
        calculator = CalculatorService()
        
        # Calculate birth base
        result = calculator.calculate_birth_base(birth_date_str)
        
        # Return calculation result
        return {
            "birth_date": birth_date_str,
            "base_number": result.get("base_number"),
            "attributes": result.get("attributes", []),
            "error": result.get("error")
        }
    
    except Exception as e:
        logger.error(f"Error processing calculator request: {str(e)}", exc_info=True)
        return {
            "birth_date": request.get("birth_date"),
            "base_number": None,
            "attributes": [],
            "error": str(e)
        }

@router.post("/reading")
async def reading_tool(
    request: Dict[str, Any],
    user_id: str = Depends(get_user_id)
) -> Dict[str, Any]:
    """
    Generate a fortune reading based on birth date and question
    
    Args:
        request: Reading request data
        user_id: User identifier from dependency
        
    Returns:
        Dictionary with fortune reading results
    """
    try:
        logger.info(f"Processing reading request with data: {json.dumps(request)}")
        
        # Extract parameters
        birth_date_str = request.get("birth_date")
        question = request.get("question", "")
        
        if not birth_date_str:
            raise HTTPException(status_code=400, detail="Birth date is required")
        
        # Get reading service
        reading_service = await get_reading_service()
        
        # Process the reading request
        from datetime import datetime
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid birth date format. Expected YYYY-MM-DD")
        
        # Get fortune reading
        reading = await reading_service.get_fortune_reading(
            birth_date=birth_date,
            user_question=question,
            user_id=user_id
        )
        
        # Return reading result
        if reading:
            return reading.dict()
        else:
            return {
                "error": "Failed to generate reading"
            }
    
    except Exception as e:
        logger.error(f"Error processing reading request: {str(e)}", exc_info=True)
        return {
            "error": str(e)
        } 