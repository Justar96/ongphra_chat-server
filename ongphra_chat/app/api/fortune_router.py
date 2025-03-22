from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.utils.fortune_tool import calculate_fortune

router = APIRouter(prefix="/fortune", tags=["Fortune"])

class FortuneRequest(BaseModel):
    birthdate: str = Field(..., description="Birthdate in DD-MM-YYYY format")
    detail_level: Optional[str] = Field("normal", description="Level of detail for the fortune calculation (simple, normal, detailed)")

class FortuneResponse(BaseModel):
    birthdate: str = Field(..., description="Formatted birthdate")
    day_of_week: str = Field(..., description="Day of the week in Thai")
    zodiac_year: str = Field(..., description="Thai zodiac year")
    base_values: Dict[str, int] = Field(..., description="Base values calculated from the birthdate")
    top_categories: Dict[str, Dict[str, Any]] = Field(..., description="Top categories for each base")
    top_pairs: list = Field(..., description="Top pairs of categories with interpretations")
    summary: str = Field(..., description="Summary of the fortune calculation")

@router.post("/calculate", response_model=FortuneResponse)
async def calculate_fortune_api(request: FortuneRequest):
    """
    Calculate fortune based on birthdate.
    
    This endpoint takes a birthdate in DD-MM-YYYY format and returns a fortune calculation,
    including day of the week, zodiac year, base values, top categories, and interpretations.
    """
    try:
        # Parse the birthdate
        try:
            birthdate = datetime.strptime(request.birthdate, "%d-%m-%Y")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid birthdate format. Please use DD-MM-YYYY.")
        
        # Calculate the fortune
        fortune_result = calculate_fortune(birthdate, request.detail_level)
        
        # Return the result
        return fortune_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating fortune: {str(e)}")

@router.get("/calculate", response_model=FortuneResponse)
async def calculate_fortune_get(
    birthdate: str = Query(..., description="Birthdate in DD-MM-YYYY format"),
    detail_level: str = Query("normal", description="Level of detail for the fortune calculation (simple, normal, detailed)")
):
    """
    Calculate fortune based on birthdate using GET method.
    
    This endpoint takes a birthdate in DD-MM-YYYY format and returns a fortune calculation,
    including day of the week, zodiac year, base values, top categories, and interpretations.
    """
    return await calculate_fortune_api(FortuneRequest(birthdate=birthdate, detail_level=detail_level)) 