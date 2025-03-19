from fastapi import APIRouter, Body, Depends, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Dict, Optional, List, Any
import uuid
import json

from app.core.logging import get_logger
from app.services.reading_service import ReadingService, get_reading_service
from app.services.response import ResponseService
from app.services.session_service import get_session_manager
from app.services.chat_service import ChatService, get_chat_service
from app.domain.meaning import FortuneReading

router = APIRouter(prefix="/api", tags=["API"])
logger = get_logger(__name__)

# Initialize ResponseService
response_service = ResponseService()

@router.post("/fortune")
async def get_fortune(
    birth_date: str = Body(..., description="Birth date in YYYY-MM-DD format"),
    thai_day: Optional[str] = Body(None, description="Thai day of birth (e.g., อาทิตย์, จันทร์). If not provided, will be determined from the birth date."),
    question: Optional[str] = Body(None, description="User's question about their fortune"),
    language: str = Body("thai", description="Response language (thai or english)"),
    user_id: Optional[str] = Body(None, description="User identifier for session tracking"),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """Get a fortune reading based on birth date and Thai day"""
    logger.info(f"Received fortune request for birth_date={birth_date}, thai_day={thai_day}")
    
    try:
        # Generate or use provided user_id
        if not user_id:
            user_id = str(uuid.uuid4())
            logger.info(f"Generated new user_id: {user_id}")
        
        # Parse birth date
        try:
            birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
        # Get session manager and save birth info to session
        session_manager = get_session_manager()
        session_manager.save_birth_info(user_id, birth_date_obj, thai_day)
        
        # Use the dedicated fortune reading method directly for better performance and reliability
        reading = await reading_service.get_fortune_reading(
            birth_date=birth_date_obj,
            thai_day=thai_day,
            question=question,
            user_id=user_id
        )
        
        # Format the reading appropriately
        response_text = f"**{reading.heading}**\n\n{reading.meaning}"
        
        return {
            "success": True,
            "text": response_text,
            "heading": reading.heading,
            "meaning": reading.meaning,
            "birth_date": reading.birth_date,
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error getting fortune: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting fortune: {str(e)}")

@router.post("/chat")
async def get_chat_response(
    prompt: str = Body(..., description="User's prompt or question"),
    birth_date: Optional[str] = Body(None, description="Birth date in YYYY-MM-DD format"),
    thai_day: Optional[str] = Body(None, description="Thai day of birth (optional, will be determined from birth date if not provided)"),
    language: str = Body("thai", description="Response language (thai or english)"),
    user_id: Optional[str] = Body(None, description="User identifier for session tracking"),
    session_id: Optional[str] = Body(None, description="Session ID for continuing a conversation"),
    enable_fortune: bool = Body(True, description="Whether to enable automatic fortune processing"),
    reading_service: ReadingService = Depends(get_reading_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get a chat response with context from previous conversations"""
    logger.info(f"Received chat request with prompt: {prompt[:50]}...")
    
    try:
        # Generate or use provided user_id
        if not user_id:
            user_id = str(uuid.uuid4())
            logger.info(f"Generated new user_id: {user_id}")
            
        # Get session manager
        session_manager = get_session_manager()
        
        # Check if we have birth info
        has_birth_info = False
        birth_date_obj = None
        
        if birth_date:
            # New birth info provided, save it
            try:
                birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
                session_manager.save_birth_info(user_id, birth_date_obj, thai_day)
                has_birth_info = True
                logger.info(f"Saved new birth info: {birth_date}, {thai_day}")
            except ValueError:
                logger.warning(f"Invalid date format: {birth_date}. Using previous birth info if available.")
        
        # Check for existing birth info in session if none provided
        if not has_birth_info:
            birth_info = session_manager.get_birth_info(user_id)
            if birth_info:
                try:
                    birth_date_obj = datetime.strptime(birth_info["birth_date"], "%Y-%m-%d")
                    thai_day = birth_info["thai_day"]
                    has_birth_info = True
                    logger.info(f"Using stored birth info: {birth_date_obj.strftime('%Y-%m-%d')}, {thai_day}")
                except (ValueError, KeyError):
                    logger.warning("Invalid stored birth info. Treating as no birth info.")
        
        # Save user message to database
        session_id, _ = await chat_service.save_message(
            user_id=user_id,
            content=prompt,
            role="user",
            session_id=session_id
        )
        
        # Use the enhanced ResponseService with fortune processing if enabled
        response_text = await response_service.generate_response(
            prompt=prompt,
            language=language,
            has_birth_info=has_birth_info,
            user_id=user_id,
            stream=False,
            process_fortune=enable_fortune
        )
        
        # Get last reading from session context to check if we just processed a fortune
        last_reading = session_manager.get_context_data(user_id, "last_reading")
        is_fortune = last_reading is not None
        
        # Get heading if available
        heading = last_reading.get("heading", "") if last_reading else ""
        
        # Save assistant response to database
        await chat_service.save_message(
            user_id=user_id,
            content=response_text,
            role="assistant",
            session_id=session_id,
            is_fortune=is_fortune,
            metadata={
                "heading": heading if is_fortune else None,
                "language": language
            }
        )
        
        return {
            "success": True,
            "text": response_text,
            "heading": heading,
            "is_fortune": is_fortune,
            "user_id": user_id,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error getting chat response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting chat response: {str(e)}")

@router.post("/chat/stream")
async def stream_chat_response(
    prompt: str = Body(..., description="User's prompt or question"),
    birth_date: Optional[str] = Body(None, description="Birth date in YYYY-MM-DD format"),
    thai_day: Optional[str] = Body(None, description="Thai day of birth (optional, will be determined from birth date if not provided)"),
    language: str = Body("thai", description="Response language (thai or english)"),
    user_id: Optional[str] = Body(None, description="User identifier for session tracking"),
    session_id: Optional[str] = Body(None, description="Session ID for continuing a conversation"),
    enable_fortune: bool = Body(True, description="Whether to enable automatic fortune processing"),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Stream a chat response with context from previous conversations"""
    logger.info(f"Received streaming chat request with prompt: {prompt[:50]}...")
    
    try:
        # Generate or use provided user_id
        if not user_id:
            user_id = str(uuid.uuid4())
            logger.info(f"Generated new user_id: {user_id}")
            
        # Get session manager
        session_manager = get_session_manager()
        
        # Check if we have birth info
        has_birth_info = False
        birth_date_obj = None
        
        if birth_date:
            # New birth info provided, save it
            try:
                birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
                session_manager.save_birth_info(user_id, birth_date_obj, thai_day)
                has_birth_info = True
                logger.info(f"Saved new birth info: {birth_date}, {thai_day}")
            except ValueError:
                logger.warning(f"Invalid date format: {birth_date}. Using previous birth info if available.")
        
        # Check for existing birth info in session if none provided
        if not has_birth_info:
            birth_info = session_manager.get_birth_info(user_id)
            if birth_info:
                try:
                    birth_date_obj = datetime.strptime(birth_info["birth_date"], "%Y-%m-%d")
                    thai_day = birth_info["thai_day"]
                    has_birth_info = True
                    logger.info(f"Using stored birth info: {birth_date_obj.strftime('%Y-%m-%d')}, {thai_day}")
                except (ValueError, KeyError):
                    logger.warning("Invalid stored birth info. Treating as no birth info.")
        
        # Save user message to database
        session_id, _ = await chat_service.save_message(
            user_id=user_id,
            content=prompt,
            role="user",
            session_id=session_id
        )
                
        # Get response generator from ResponseService
        streaming_generator = await response_service.generate_response(
            prompt=prompt,
            language=language,
            has_birth_info=has_birth_info,
            user_id=user_id,
            stream=True,
            process_fortune=enable_fortune  # Pass the enable_fortune parameter
        )
        
        # Create a wrapper generator to save the full response
        async def stream_and_save():
            full_response = ""
            
            # Stream the response chunks
            async for chunk in streaming_generator:
                # Add to full response
                full_response += chunk
                
                # Yield the chunk to the client
                yield chunk
            
            # After streaming completes, check if this was a fortune reading
            last_reading = session_manager.get_context_data(user_id, "last_reading")
            is_fortune = last_reading is not None
            
            # Get heading if available
            heading = last_reading.get("heading", "") if last_reading else ""
            
            # Save complete response to database
            await chat_service.save_message(
                user_id=user_id,
                content=full_response,
                role="assistant",
                session_id=session_id,
                is_fortune=is_fortune,
                metadata={
                    "heading": heading if is_fortune else None,
                    "language": language,
                    "streamed": True
                }
            )
            
            # Send end marker
            yield "[DONE]"
        
        # Create a streaming response
        return StreamingResponse(
            stream_and_save(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error getting streaming chat response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting streaming chat response: {str(e)}")
    
@router.delete("/session/{user_id}")
async def clear_session(
    user_id: str = Path(..., description="User ID to clear"),
    session_id: Optional[str] = Query(None, description="Specific session ID to clear (if not provided, all sessions will be marked inactive)"),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Clear user session data"""
    try:
        # Clear memory session
        session_manager = get_session_manager()
        memory_cleared = session_manager.clear_session(user_id)
        
        # Also clear from response service
        response_service.clear_user_conversation(user_id)
        
        # Handle database session(s)
        db_cleared = False
        if session_id:
            # End specific session
            db_cleared = await chat_service.end_session(session_id)
            message = f"Session {session_id} for user {user_id} has been ended"
        else:
            # Get active sessions and end them all
            sessions = await chat_service.get_all_user_sessions(user_id, active_only=True)
            for session in sessions:
                await chat_service.end_session(session.id)
            db_cleared = True
            message = f"All active sessions for user {user_id} have been ended"
        
        return {
            "success": memory_cleared and db_cleared,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@router.get("/session/{user_id}/context")
async def get_session_context(user_id: str = Path(..., description="User ID to get context for")):
    """Get user session context data"""
    try:
        # Get session manager
        session_manager = get_session_manager()
        
        # Get birth info
        birth_info = session_manager.get_birth_info(user_id)
        
        # Get recent topics
        recent_topics = session_manager.get_recent_topics(user_id)
        
        # Get last reading
        last_reading = session_manager.get_context_data(user_id, "last_reading")
        
        # Get conversation history (summarized)
        history = session_manager.get_conversation_history(user_id)
        conversation_summary = [
            {"role": msg["role"], "content": msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]}
            for msg in history[-5:]  # Show last 5 messages
        ]
        
        return {
            "success": True,
            "user_id": user_id,
            "birth_info": birth_info,
            "recent_topics": recent_topics,
            "last_reading": last_reading,
            "conversation_summary": conversation_summary,
            "conversation_length": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting session context: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting session context: {str(e)}")

@router.post("/birth-chart/enriched")
async def get_enriched_birth_chart(
    birth_date: str = Body(..., description="Birth date in YYYY-MM-DD format"),
    thai_day: Optional[str] = Body(None, description="Thai day of birth (e.g., อาทิตย์, จันทร์). If not provided, will be determined from the birth date."),
    question: Optional[str] = Body(None, description="User's question for focused readings"),
    user_id: Optional[str] = Body(None, description="User identifier for session tracking"),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """Get an enriched birth chart with calculator results and category details"""
    logger.info(f"Received enriched birth chart request for birth_date={birth_date}, thai_day={thai_day}")
    
    try:
        # Generate or use provided user_id
        if not user_id:
            user_id = str(uuid.uuid4())
            logger.info(f"Generated new user_id: {user_id}")
        
        # Parse birth date
        try:
            birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
        # Get session manager for tracking
        session_manager = get_session_manager()
        session_manager.save_birth_info(user_id, birth_date_obj, thai_day)
        
        # Get meaning service and generate enriched birth chart
        from app.services.meaning import MeaningService
        from app.repository.category_repository import CategoryRepository
        from app.repository.reading_repository import ReadingRepository
        
        # Initialize repositories and service
        category_repository = CategoryRepository()
        reading_repository = ReadingRepository()
        meaning_service = MeaningService(
            category_repository=category_repository,
            reading_repository=reading_repository
        )
        
        # Generate enriched birth chart
        result = await meaning_service.get_enriched_birth_chart(
            birth_date=birth_date_obj,
            thai_day=thai_day,
            question=question
        )
        
        # Save birth chart info in session for future reference
        session_manager.save_context_data(user_id, "enriched_birth_chart", {
            "birth_date": birth_date,
            "thai_day": thai_day,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating enriched birth chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating enriched birth chart: {str(e)}") 