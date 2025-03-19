# app/routers/ai_tools_router.py
from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Optional, Any

from app.core.logging import get_logger
from app.utils.ai_tools import process_fortune_tool

# Initialize router
router = APIRouter(prefix="/ai-tools", tags=["AI Tools"])
logger = get_logger(__name__)

@router.post("/process-fortune")
async def process_fortune(
    user_message: str = Body(..., description="The user's message to analyze"),
    user_id: Optional[str] = Body(None, description="Optional user ID for session tracking")
) -> Dict[str, Any]:
    """
    Process a potential fortune reading request.
    
    This endpoint:
    1. Analyzes the user's message to determine if it's a fortune request
    2. Checks if birth date is available or can be extracted
    3. Either asks for birth date or processes the fortune reading
    
    Args:
        user_message: The user's message
        user_id: Optional user ID for session tracking
        
    Returns:
        A structured response with fortune reading information or instructions
    """
    logger.info(f"AI tool endpoint called: process-fortune")
    
    try:
        # Process the fortune request
        result = await process_fortune_tool(user_message, user_id)
        
        return result
    except Exception as e:
        logger.error(f"Error processing fortune request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing fortune request: {str(e)}") 