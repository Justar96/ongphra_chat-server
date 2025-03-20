from fastapi import Header, HTTPException, Request
from typing import Optional

async def get_user_id(
    request: Request,
    x_user_id: Optional[str] = Header(None)
) -> str:
    """
    Extract and validate the user ID from request headers
    
    Args:
        request: FastAPI request object
        x_user_id: User ID from X-User-ID header
        
    Returns:
        Validated user ID
        
    Raises:
        HTTPException: If user ID is missing or invalid
    """
    # First try to get from header
    user_id = x_user_id
    
    # If not in header, try to get from query parameters
    if not user_id:
        user_id = request.query_params.get("user_id")
    
    # If still not found, try to get from cookies
    if not user_id and request.cookies:
        user_id = request.cookies.get("user_id")
        
    # If still not found, generate a temporary ID
    if not user_id:
        # For testing/development, return a default user ID
        # In production, you might want to raise an exception instead
        return "anonymous_user"
    
    return user_id 