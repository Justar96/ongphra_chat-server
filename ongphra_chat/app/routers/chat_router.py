# app/routers/chat_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import uuid

from app.services.chat_service import ChatService, get_chat_service
from app.domain.chat import ChatSession, ChatMessage, ChatHistoryRequest, ChatHistoryResponse

router = APIRouter(prefix="/chat", tags=["Chat History"])

@router.get("/sessions", summary="Get user's chat sessions")
async def get_user_sessions(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    active_only: bool = Query(True),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get a list of chat sessions for a user
    
    Args:
        user_id: User identifier
        limit: Maximum number of sessions to return (1-50)
        active_only: If true, only return active sessions
        
    Returns:
        List of chat sessions
    """
    sessions = await chat_service.get_all_user_sessions(
        user_id=user_id,
        limit=limit,
        active_only=active_only
    )
    
    return {
        "success": True,
        "sessions": [session.to_dict() for session in sessions],
        "count": len(sessions)
    }

@router.get("/history", summary="Get chat history")
async def get_chat_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get chat history for a user
    
    Args:
        user_id: User identifier
        session_id: Optional session ID (will use most recent active session if not provided)
        limit: Maximum number of messages to return (1-100)
        
    Returns:
        Chat session and messages
    """
    session, messages = await chat_service.get_conversation_history(
        user_id=user_id,
        session_id=session_id,
        limit=limit
    )
    
    if not session:
        if session_id:
            return {
                "success": False,
                "error": f"Session {session_id} not found for user {user_id}"
            }
        else:
            return {
                "success": False,
                "error": f"No active sessions found for user {user_id}"
            }
    
    return {
        "success": True,
        "session": session.to_dict(),
        "messages": [msg.to_dict() for msg in messages],
        "count": len(messages)
    }

@router.post("/end-session", summary="End a chat session")
async def end_chat_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Mark a chat session as inactive
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success status
    """
    success = await chat_service.end_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return {
        "success": True,
        "message": f"Session {session_id} marked as inactive"
    }

@router.delete("/session/{session_id}", summary="Delete a chat session")
async def delete_chat_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete a chat session and all its messages
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success status
    """
    success = await chat_service.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return {
        "success": True,
        "message": f"Session {session_id} and all its messages deleted"
    } 