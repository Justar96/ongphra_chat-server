# app/utils/ai_tools.py
from typing import Dict, Any
import json

from app.core.logging import get_logger
from app.utils.fortune_tool import handle_fortune_request

logger = get_logger(__name__)

async def process_fortune_tool(user_message: str, user_id: str = None) -> Dict[str, Any]:
    """
    Tool for AI to determine if a user is requesting a fortune reading and process accordingly.
    
    This tool:
    1. Analyzes the user's message to detect fortune-related requests
    2. Checks if birth date information is available or can be extracted from the message
    3. Returns a structured response that tells the AI what to do next
    
    Args:
        user_message: The user's message or question
        user_id: Optional user identifier for session tracking
        
    Returns:
        A structured response with the following fields:
        - needs_birthdate: Boolean indicating if we need to ask for birth date
        - is_fortune_request: Boolean indicating if this is a fortune request
        - fortune_reading: Fortune reading result if available, including:
            - birth_date: Birth date used for the reading
            - thai_day: Thai day of the birth date
            - question: User's question
            - heading: Reading heading
            - meaning: Reading content
            - influence_type: Type of influence (positive, negative, neutral)
        - user_message: Original user message
        - extracted_birthdate: Birth date extracted from message (if any)
    """
    logger.info(f"Processing potential fortune request: '{user_message[:50]}...'")
    
    try:
        # Call the fortune handler function
        result = await handle_fortune_request(user_message, user_id)
        
        # Log the result summary
        if result["is_fortune_request"]:
            if result["needs_birthdate"]:
                logger.info("Fortune request identified, but need birth date")
            elif result["fortune_reading"]:
                logger.info(f"Fortune reading processed successfully: {result['fortune_reading']['heading'][:50]}...")
        else:
            logger.info("Not a fortune request")
            
        return result
        
    except Exception as e:
        logger.error(f"Error in process_fortune_tool: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "is_fortune_request": False,
            "needs_birthdate": False,
            "user_message": user_message,
            "fortune_reading": None
        }
        
def get_available_ai_tools() -> Dict[str, Any]:
    """
    Get a dictionary of all available AI tools
    
    Returns:
        Dictionary mapping tool names to their function references
    """
    return {
        "process_fortune": process_fortune_tool
    } 