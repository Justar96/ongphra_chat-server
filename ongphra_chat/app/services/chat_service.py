import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging
from fastapi import Depends
import json

from app.models.database import ChatSession, ChatMessage
from app.config.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatService:
    """Service for managing chat conversations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, user_id: str, title: Optional[str] = None, id: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        try:
            session_id = id or str(uuid.uuid4())
            metadata = {"title": title} if title else {}
            
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                meta_data=json.dumps(metadata) if metadata else None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            return session
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            self.db.rollback()
            raise
    
    async def create_session_async(self, user_id: str, title: Optional[str] = None, id: Optional[str] = None) -> ChatSession:
        """Create a new chat session asynchronously"""
        try:
            session_id = id or str(uuid.uuid4())
            metadata = {"title": title} if title else {}
            
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                meta_data=json.dumps(metadata) if metadata else None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            return session
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            self.db.rollback()
            raise
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        try:
            return self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        except Exception as e:
            logger.error(f"Error getting chat session: {str(e)}")
            return None
    
    async def get_session_async(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID asynchronously"""
        try:
            return self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        except Exception as e:
            logger.error(f"Error getting chat session: {str(e)}")
            return None
    
    def get_active_session(self, user_id: str) -> Optional[ChatSession]:
        """Get the active chat session for a user"""
        try:
            return self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).order_by(desc(ChatSession.created_at)).first()
        except Exception as e:
            logger.error(f"Error getting active chat session: {str(e)}")
            return None
    
    async def get_active_session_async(self, user_id: str) -> Optional[ChatSession]:
        """Get the active chat session for a user asynchronously"""
        try:
            return self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).order_by(desc(ChatSession.created_at)).first()
        except Exception as e:
            logger.error(f"Error getting active chat session: {str(e)}")
            return None
    
    def update_session_title(self, session_id: str, title: str) -> Optional[ChatSession]:
        """Update the title of a chat session"""
        session = self.get_session(session_id)
        if session:
            try:
                metadata = json.loads(session.meta_data) if session.meta_data else {}
            except:
                metadata = {}
            
            metadata["title"] = title
            session.meta_data = json.dumps(metadata)
            self.db.commit()
            self.db.refresh(session)
        return session
    
    def end_session(self, session_id: str) -> Optional[ChatSession]:
        """Mark a chat session as inactive"""
        session = self.get_session(session_id)
        if session:
            session.is_active = False
            self.db.commit()
            self.db.refresh(session)
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages"""
        session = self.get_session(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False
    
    def add_message(self, session_id: str, user_id: str, role: str, content: str, is_fortune: bool = False) -> ChatMessage:
        """Add a message to a chat session"""
        try:
            # Get the sequence number by counting existing messages
            sequence = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .count() + 1
            )
            
            metadata = {"sequence": sequence}
            
            message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                is_fortune=is_fortune,
                meta_data=json.dumps(metadata)
            )
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            # Update session's updated_at timestamp
            session = self.get_session(session_id)
            if session:
                session.updated_at = datetime.now()
                self.db.commit()
            
            return message
        except Exception as e:
            logger.error(f"Error adding chat message: {str(e)}")
            self.db.rollback()
            raise
    
    async def add_message_async(self, session_id: str, user_id: str, role: str, content: str, is_fortune: bool = False) -> ChatMessage:
        """Add a message to a chat session asynchronously"""
        try:
            # Get the sequence number by counting existing messages
            sequence = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .count() + 1
            )
            
            metadata = {"sequence": sequence}
            
            message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                is_fortune=is_fortune,
                meta_data=json.dumps(metadata),
                created_at=datetime.now()
            )
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            # Update session's updated_at timestamp
            session = await self.get_session_async(session_id)
            if session:
                session.updated_at = datetime.now()
                self.db.commit()
            
            return message
        except Exception as e:
            logger.error(f"Error adding chat message: {str(e)}")
            self.db.rollback()
            raise
    
    def get_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        """Get all messages for a chat session ordered by creation time"""
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
            .all()
        )
    
    def get_message_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get message history for a chat session in OpenAI format"""
        messages = self.get_messages(session_id)
        return [msg.to_openai_message() for msg in messages]
    
    def get_all_user_sessions(self, user_id: str, limit: int = 20) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
            .all()
        )
    
    def get_conversation_history(self, session_id: str, limit: int = 100) -> List[Dict[str, str]]:
        """Get conversation history for a chat session"""
        try:
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at).limit(limit).all()
            
            # Convert to format expected by OpenAI
            return [{"role": msg.role, "content": msg.content} for msg in messages]
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    async def get_conversation_history_async(self, session_id: str, limit: int = 100) -> List[Dict[str, str]]:
        """Get conversation history for a chat session asynchronously"""
        try:
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at).limit(limit).all()
            
            # Convert to format expected by OpenAI
            return [{"role": msg.role, "content": msg.content} for msg in messages]
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

# Dependency to get chat service
def get_chat_service(db: Session = Depends(get_db)):
    return ChatService(db) 