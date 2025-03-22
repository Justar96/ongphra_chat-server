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
import asyncio

from app.services.chat_service import ChatService, get_chat_service
from app.utils.openai_client import OpenAIClient, get_openai_client
from app.models.schemas import Message, ChatMessageRequest, ChatResponse, ResponseStatus, ChatChoice, ChatCompletion, StreamingChatRequest, StreamingChatResponse
from app.config.database import get_db
from app.utils.tool_handler import tool_handler, ToolResult

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
    chat_service: ChatService = Depends(get_chat_service),
    db: Session = Depends(get_db)
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
        # Get or create session
        session_id = request.session_id
        user_id = request.user_id or str(uuid.uuid4())
        
        if not session_id:
            # Create a new session if not provided
            session = chat_service.create_session(user_id)
            session_id = session.id
        
        # Check if session exists
        else:
            session = chat_service.get_session(session_id)
            if not session:
                # Create a new session with the provided ID
                session = chat_service.create_session(user_id, id=session_id)
        
        # Process message with tool handler first to check for special commands
        tool_result = None
        
        # Check if the message appears to be a birthdate request
        if any(keyword in request.message.lower() for keyword in ["birthdate", "birth date", "fortune", "ดูดวง", "วันเกิด"]):
            # Extract potential birthdate from message
            import re
            birthdate_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', request.message)
            
            if birthdate_match:
                birthdate = birthdate_match.group(1)
                # Convert DD/MM/YYYY to YYYY-MM-DD if needed
                if '/' in birthdate:
                    parts = birthdate.split('/')
                    if len(parts) == 3 and len(parts[2]) == 4:
                        day, month, year = parts
                        birthdate = f"{year}-{month}-{day}"
                
                # Execute the fortune tool
                tool_result = await tool_handler.execute_tool(
                    "fortune_calculator", 
                    birthdate=birthdate,
                    detail_level="normal"
                )
                
                # If the tool was successful, prepare a user-friendly response
                if tool_result and not tool_result.error:
                    # Get fortune data
                    fortune_data = tool_result.result.get("fortune", {})
                    
                    # Compose a response for the user
                    if "summary" in fortune_data:
                        # Get RAG interpretations if available
                        rag_interps = fortune_data.get("rag_interpretations", [])
                        rag_insights = "\n\n".join([f"- {interp.get('interpretation')}" for interp in rag_interps[:3]]) if rag_interps else ""
                        
                        # Prepare detailed response using fortune data
                        message_response = f"🔮 **ผลการดูดวงชะตาของคุณ**\n\n{fortune_data.get('summary')}"
                        
                        if rag_insights:
                            message_response += f"\n\n**ข้อมูลเชิงลึกเพิ่มเติม:**\n{rag_insights}"
                        
                        # Include pairs/combinations if available
                        combinations = fortune_data.get("combination_interpretations", [])
                        if combinations:
                            message_response += f"\n\n**ความสัมพันธ์สำคัญในดวงชะตา:**\n"
                            for i, combo in enumerate(combinations[:2]):  # Show top 2 combinations
                                message_response += f"\n**{combo.get('heading')}**\n{combo.get('meaning')}\n"
                        
                        # Save the user message
                        chat_service.add_message(
                            session_id=session_id,
                            user_id=user_id,
                            role="user",
                            content=request.message
                        )
                        
                        # Save the assistant's response
                        chat_service.add_message(
                            session_id=session_id,
                            user_id=user_id,
                            role="assistant",
                            content=message_response
                        )
                        
                        # Create a tool result with handled flag and response
                        tool_result = ToolResult(
                            tool_name="fortune_calculator",
                            result=tool_result.result,
                            error=None
                        )
                        
                        # Add handled and data attributes that the router expects
                        tool_result.handled = True
                        tool_result.response = message_response
                        tool_result.data = fortune_data
                        tool_result.modified_message = None
        
        # If a tool handled the message
        if tool_result and not tool_result.error:
            # If a tool fully handled the message and streaming is requested
            if tool_result.handled and request.stream:
                # Save the user message
                chat_service.add_message(
                    session_id=session_id,
                    user_id=user_id,
                    role="user",
                    content=request.message
                )
                
                # Generate a message ID for the response
                message_id = str(uuid.uuid4())
                
                # Save the assistant's response from the tool
                if tool_result.response:
                    chat_service.add_message(
                        session_id=session_id,
                        user_id=user_id,
                        role="assistant",
                        content=tool_result.response
                    )
                
                # Create streaming response function for tool result
                async def stream_tool_result():
                    # Connected status
                    yield f"data: {json.dumps({'status': 'connected', 'session_id': session_id})}\n\n"
                    
                    # If we have a tool response, simulate streaming it character by character
                    if tool_result.response:
                        # Simulate streaming by breaking the response into chunks
                        response_text = tool_result.response
                        chunk_size = max(1, len(response_text) // 10)  # Divide into ~10 chunks
                        
                        for i in range(0, len(response_text), chunk_size):
                            chunk = response_text[i:i+chunk_size]
                            yield f"data: {json.dumps({'status': 'streaming', 'message_id': message_id, 'session_id': session_id, 'user_id': user_id, 'content': chunk})}\n\n"
                            await asyncio.sleep(0.1)  # Add a small delay to simulate streaming
                    
                    # Complete response
                    complete_data = {
                        'status': 'complete',
                        'message_id': message_id,
                        'session_id': session_id,
                        'user_id': user_id,
                        'content': '',
                        'complete_response': tool_result.response or '',
                        'tool_result': tool_result.data
                    }
                    yield f"data: {json.dumps(complete_data)}\n\n"
                
                # Return streaming response
                response = StreamingResponse(
                    stream_tool_result(),
                    media_type="text/event-stream"
                )
                
                # Add SSE headers
                response.headers["Cache-Control"] = "no-cache"
                response.headers["Connection"] = "keep-alive"
                response.headers["X-Accel-Buffering"] = "no"
                
                return response
            
            # If a tool fully handled the message but no streaming is requested
            elif tool_result.handled:
                logger.info(f"Message handled by tool: {tool_result}")
                
                # Save the user message
                chat_service.add_message(
                    session_id=session_id,
                    user_id=user_id,
                    role="user",
                    content=request.message
                )
                
                # Generate a message ID for the response
                message_id = str(uuid.uuid4())
                
                # Save the assistant's response from the tool
                if tool_result.response:
                    chat_service.add_message(
                        session_id=session_id,
                        user_id=user_id,
                        role="assistant",
                        content=tool_result.response
                    )
                
                # Create a chat completion from the tool result
                chat_completion = ChatCompletion(
                    id=f"tool-{message_id}",
                    created=int(datetime.now().timestamp()),
                    model="tool-handler",
                    choices=[
                        ChatChoice(
                            index=0,
                            message={"role": "assistant", "content": tool_result.response or ""},
                            finish_reason="tool_completion"
                        )
                    ],
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                )
                
                # Return the response
                return ChatResponse(
                    status=ResponseStatus(success=True),
                    message_id=message_id,
                    response=chat_completion,
                    user_id=user_id,
                    session_id=session_id,
                    tool_result=tool_result.data
                )
            
            # Use the modified message if provided by the tool
            message = tool_result.modified_message or request.message
            
            # Create a simple message structure
            messages = [{"role": "user", "content": message}]
            
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
        else:
            # Use the modified message if provided by the tool
            message = request.message
            if tool_result and hasattr(tool_result, 'modified_message') and tool_result.modified_message:
                message = tool_result.modified_message
            
            # Create a simple message structure
            messages = [{"role": "user", "content": message}]
            
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

@router.post("/stream", summary="Stream a chat conversation (POST method)")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    openai_client: OpenAIClient = Depends(get_openai_client),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        # Convert Pydantic models to dictionaries
        messages = [msg.to_dict() for msg in chat_request.messages]
        
        # Generate user_id and session_id if not provided
        user_id = chat_request.user_id or str(uuid.uuid4())
        
        # Get or create session
        if chat_request.session_id:
            session = chat_service.get_session(chat_request.session_id)
            # If session doesn't exist but ID was provided, create with that ID
            if not session:
                session = chat_service.create_session(user_id, id=chat_request.session_id)
            session_id = session.id
        else:
            # Get active session or create new one
            session = chat_service.get_active_session(user_id)
            if not session:
                session = chat_service.create_session(user_id)
            session_id = session.id
        
        # Handle streaming response
        if chat_request.stream:
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

@router.get("/stream", summary="Stream a chat conversation (GET method for EventSource)")
async def chat_stream_get(
    message: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    openai_client: OpenAIClient = Depends(get_openai_client),
    chat_service: ChatService = Depends(get_chat_service)
):
    try:
        # Create a simple message structure similar to the POST endpoint
        chat_request = {
            "message": message,
            "user_id": user_id,
            "session_id": session_id
        }
        
        # Get or create session
        session = await chat_service.get_or_create_session(user_id, session_id)
        session_id = session.id
        
        # Save user message
        message_id = str(uuid.uuid4())
        await openai_client.save_message(session_id, user_id, "user", message, message_id)
        
        # Get streaming response from OpenAI
        async def generate():
            try:
                # Send SSE headers for EventSource compatibility
                yield "data: {\"status\":\"connected\",\"session_id\":\"" + session_id + "\"}\n\n"
                
                # Stream completion
                async for chunk in openai_client.stream_chat_completion(session_id):
                    if "content" in chunk and chunk["content"]:
                        response_data = {
                            "status": "streaming",
                            "message_id": message_id,
                            "session_id": session_id,
                            "user_id": user_id,
                            "content": chunk["content"]
                        }
                        yield f"data: {json.dumps(response_data)}\n\n"
                
                # Complete response
                complete_response = await openai_client.get_last_assistant_message(session_id)
                complete_data = {
                    "status": "complete",
                    "message_id": message_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "content": "",
                    "complete_response": complete_response
                }
                yield f"data: {json.dumps(complete_data)}\n\n"
                
            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                error_data = {
                    "status": "error",
                    "message_id": message_id,
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        # Configure CORS headers for SSE
        response = StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"
        response.headers["X-Accel-Buffering"] = "no"
        
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat_stream_get: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ws-available", summary="Check if WebSocket chat is available")
async def websocket_available():
    """Check if WebSocket chat endpoint is available"""
    return {
        "status": ResponseStatus(success=False),
        "available": False,
        "message": "WebSocket chat is no longer available. Please use HTTP streaming."
    }

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