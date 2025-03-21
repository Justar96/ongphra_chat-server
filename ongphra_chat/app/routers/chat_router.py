# app/routers/chat_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any, Union
import uuid
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import json
from datetime import datetime
import logging

from app.services.chat_service import ChatService, get_chat_service
from app.utils.openai_client import OpenAIClient, get_openai_client
from app.models.schemas import Message, ChatMessageRequest, ChatResponse, ResponseStatus, ChatChoice, ChatCompletion, StreamingChatRequest, StreamingChatResponse
from app.config.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# Request Models
class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: Optional[str] = Field(default=None, description="User identifier for tracking conversations")
    session_id: Optional[str] = Field(default=None, description="Session identifier for tracking conversations")
    stream: bool = Field(default=False, description="Whether to stream the response")

@router.post("", summary="Send a chat message to the AI", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    openai_client: OpenAIClient = Depends(get_openai_client),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message or conversation history to the AI and get a response.
    
    For single message conversations, just include one message with role 'user'.
    For multi-message conversations, include the full history in the correct order.
    
    Args:
        messages: List of messages in the conversation
        user_id: Optional user identifier for tracking conversations
        session_id: Optional session identifier for tracking conversations
        stream: Whether to stream the response
        
    Returns:
        AI response or streaming response
    """
    try:
        # Convert Pydantic models to dictionaries
        messages = [msg.to_dict() for msg in request.messages]
        
        # Generate user_id and session_id if not provided
        user_id = request.user_id or str(uuid.uuid4())
        
        # Get or create session
        if request.session_id:
            session = chat_service.get_session(request.session_id)
            # If session doesn't exist but ID was provided, create with that ID
            if not session:
                session = chat_service.create_session(user_id, id=request.session_id)
            session_id = session.id
        else:
            # Get active session or create new one
            session = chat_service.get_active_session(user_id)
            if not session:
                session = chat_service.create_session(user_id)
            session_id = session.id
        
        # Handle streaming response
        if request.stream:
            async def stream_generator():
                async for chunk in openai_client.stream_chat_completion(
                    messages=messages, 
                    user_id=user_id,
                    session_id=session_id
                ):
                    yield json.dumps(chunk.dict()) + "\n"
                    
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
        # Handle regular response
        openai_response = await openai_client.chat_completion(messages, session_id=session_id, user_id=user_id, stream=False)
        
        # Convert to ChatCompletion model
        chat_completion = ChatCompletion(
            id=openai_response["id"],
            created=openai_response["created"],
            model=openai_response["model"],
            choices=[
                ChatChoice(
                    index=i,
                    message=choice["message"],
                    finish_reason=choice["finish_reason"]
                )
                for i, choice in enumerate(openai_response["choices"])
            ],
            usage=openai_response.get("usage", None)
        )
        
        # Create response
        return ChatResponse(
            status=ResponseStatus(success=True),
            message_id=str(uuid.uuid4()),
            response=chat_completion,
            user_id=user_id,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/message", summary="Send a message to the chatbot", response_model=ChatResponse)
async def chat_message(
    request: ChatMessageRequest,
    openai_client: OpenAIClient = Depends(get_openai_client),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to the chatbot and get a response
    
    Args:
        message: User's message
        user_id: Optional user ID for conversation tracking
        session_id: Optional session ID for conversation tracking
        stream: Whether to stream the response
        
    Returns:
        Chatbot response
    """
    try:
        # Create a simple message structure
        messages = [{"role": "user", "content": request.message}]
        
        # Generate user_id and session_id if not provided
        user_id = request.user_id or str(uuid.uuid4())
        
        # Get or create session
        if request.session_id:
            session = chat_service.get_session(request.session_id)
            # If session doesn't exist but ID was provided, create with that ID
            if not session:
                session = chat_service.create_session(user_id, id=request.session_id)
            session_id = session.id
        else:
            # Get active session or create new one
            session = chat_service.get_active_session(user_id)
            if not session:
                session = chat_service.create_session(user_id)
            session_id = session.id
        
        # Handle streaming response
        if request.stream:
            async def stream_generator():
                async for chunk in openai_client.stream_chat_completion(
                    messages=messages, 
                    user_id=user_id,
                    session_id=session_id
                ):
                    yield json.dumps(chunk.dict()) + "\n"
                    
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
        # Handle regular response
        response = await openai_client.chat_completion(
            messages=messages,
            user_id=user_id,
            session_id=session_id
        )
        
        # Create a response object using the ChatCompletion model
        chat_completion = ChatCompletion(
            id=response["id"],
            created=response["created"],
            model=response["model"],
            choices=[
                ChatChoice(
                    index=0,
                    message=response["choices"][0]["message"],
                    finish_reason=response["choices"][0]["finish_reason"]
                )
            ],
            usage=response["usage"]
        )
        
        # Create response
        return ChatResponse(
            status=ResponseStatus(success=True),
            message_id=str(uuid.uuid4()),
            response=chat_completion,
            user_id=user_id,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.post("/stream", summary="Stream a chat conversation")
async def chat_stream(
    request: ChatMessageRequest,
    openai_client: OpenAIClient = Depends(get_openai_client),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to the chatbot and get a streaming response
    
    Args:
        message: User's message
        user_id: Optional user ID for conversation tracking
        session_id: Optional session ID for conversation tracking
        
    Returns:
        Streaming response from the chatbot
    """
    try:
        # Create a simple message structure
        messages = [{"role": "user", "content": request.message}]
        
        # Generate user_id and session_id if not provided
        user_id = request.user_id or str(uuid.uuid4())
        
        # Get or create session
        if request.session_id:
            session = chat_service.get_session(request.session_id)
            # If session doesn't exist but ID was provided, create with that ID
            if not session:
                session = chat_service.create_session(user_id, id=request.session_id)
            session_id = session.id
        else:
            # Get active session or create new one
            session = chat_service.get_active_session(user_id)
            if not session:
                session = chat_service.create_session(user_id)
            session_id = session.id
        
        # Return a streaming response
        async def stream_generator():
            async for chunk in openai_client.stream_chat_completion(
                messages=messages, 
                user_id=user_id,
                session_id=session_id
            ):
                yield f"data: {json.dumps(chunk.dict())}\n\n"
                
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error processing streaming request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing streaming request: {str(e)}")

@router.get("/sessions", summary="Get user's chat sessions")
async def get_user_sessions(
    user_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get a list of chat sessions for a user"""
    try:
        sessions = chat_service.get_all_user_sessions(user_id)
        
        return {
            "status": ResponseStatus(success=True),
            "sessions": [session.to_dict() for session in sessions],
            "count": len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")

@router.get("/history", summary="Get chat history")
async def get_chat_history(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get chat history for a session"""
    try:
        # First check if session exists
        session = chat_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
        # Get messages with limit
        messages = chat_service.get_messages(session_id, limit=limit)
        
        # Convert messages to dictionaries with proper error handling
        message_dicts = []
        for msg in messages:
            try:
                message_dicts.append(msg.to_dict())
            except Exception as e:
                logger.error(f"Error converting message to dict: {str(e)}")
                # Create a simplified dict if to_dict fails
                message_dicts.append({
                    "id": msg.id,
                    "session_id": msg.session_id,
                    "user_id": msg.user_id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    "is_fortune": getattr(msg, "is_fortune", False)
                })
        
        return {
            "status": ResponseStatus(success=True),
            "session": session.to_dict(),
            "messages": message_dicts,
            "count": len(messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@router.post("/end-session", summary="End a chat session")
async def end_chat_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Mark a chat session as inactive"""
    try:
        session = chat_service.end_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return {
            "status": ResponseStatus(success=True),
            "message": f"Session {session_id} marked as inactive",
            "session": session.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")

@router.delete("/session/{session_id}", summary="Delete a chat session")
async def delete_chat_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Delete a chat session and all its messages"""
    try:
        result = chat_service.delete_session(session_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return {
            "status": ResponseStatus(success=True),
            "message": f"Session {session_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

@router.post("/new-session", summary="Create a new chat session")
async def create_new_session(
    user_id: str = Body(..., embed=True),
    title: Optional[str] = Body(None, embed=True),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a new chat session"""
    try:
        session = chat_service.create_session(user_id, title)
        
        return {
            "status": ResponseStatus(success=True),
            "message": "New session created",
            "session": session.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@router.put("/session/{session_id}/title", summary="Update session title")
async def update_session_title(
    session_id: str,
    title: str = Body(..., embed=True),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Update the title of a chat session"""
    try:
        session = chat_service.update_session_title(session_id, title)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return {
            "status": ResponseStatus(success=True),
            "message": "Session title updated",
            "session": session.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating session title: {str(e)}") 