# app/services/chat_service.py
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

from app.core.logging import get_logger
from app.repository.chat_repository import ChatRepository
from app.domain.chat import ChatSession, ChatMessage


class ChatService:
    """Service for managing chat sessions and history"""
    
    def __init__(self, chat_repository: ChatRepository):
        """Initialize the chat service"""
        self.chat_repository = chat_repository
        self.logger = get_logger(__name__)
        self.logger.info("Initialized ChatService")
    
    async def get_or_create_session(self, user_id: str) -> str:
        """
        Get the most recent active session for a user or create a new one
        
        Args:
            user_id: User identifier
            
        Returns:
            Session ID
        """
        # Try to get the most recent active session
        sessions = await self.chat_repository.get_user_sessions(user_id, limit=1, active_only=True)
        
        if sessions:
            self.logger.info(f"Using existing session {sessions[0].id} for user {user_id}")
            return sessions[0].id
        
        # Create a new session if none exists
        session_id = await self.chat_repository.create_session(user_id)
        self.logger.info(f"Created new session {session_id} for user {user_id}")
        
        return session_id
    
    async def save_message(
        self, 
        user_id: str, 
        content: str, 
        role: str, 
        session_id: Optional[str] = None,
        is_fortune: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """
        Save a message to a session
        
        Args:
            user_id: User identifier
            content: Message content
            role: Message role (user or assistant)
            session_id: Optional session ID (will be created if not provided)
            is_fortune: Whether this message contains a fortune reading
            metadata: Optional additional message metadata
            
        Returns:
            Tuple of (session_id, message_id)
        """
        # Get or create a session
        if not session_id:
            session_id = await self.get_or_create_session(user_id)
            
        # Add the message
        message_id = await self.chat_repository.add_message(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            is_fortune=is_fortune,
            metadata=metadata
        )
        
        self.logger.info(f"Saved {role} message to session {session_id}")
        
        return session_id, message_id
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> Tuple[Optional[ChatSession], List[ChatMessage]]:
        """
        Get conversation history for a user
        
        Args:
            user_id: User identifier
            session_id: Optional session ID (will use most recent active session if not provided)
            limit: Maximum number of messages to return
            
        Returns:
            Tuple of (session, messages)
        """
        # Get the session
        if not session_id:
            sessions = await self.chat_repository.get_user_sessions(user_id, limit=1, active_only=True)
            if not sessions:
                self.logger.info(f"No active sessions found for user {user_id}")
                return None, []
            
            session_id = sessions[0].id
        
        session = await self.chat_repository.get_session(session_id)
        if not session:
            self.logger.warning(f"Session {session_id} not found")
            return None, []
        
        # Get the messages
        messages = await self.chat_repository.get_session_messages(session_id, limit=limit)
        
        return session, messages
    
    async def get_all_user_sessions(self, user_id: str, limit: int = 10, active_only: bool = True) -> List[ChatSession]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            active_only: Whether to return only active sessions
            
        Returns:
            List of ChatSession objects
        """
        return await self.chat_repository.get_user_sessions(user_id, limit=limit, active_only=active_only)
    
    async def end_session(self, session_id: str) -> bool:
        """
        Mark a session as inactive
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        return await self.chat_repository.update_session(session_id, is_active=False)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        return await self.chat_repository.delete_session(session_id)


# Factory function for dependency injection
def get_chat_service() -> ChatService:
    """Get chat service instance"""
    chat_repository = ChatRepository()
    return ChatService(chat_repository) 