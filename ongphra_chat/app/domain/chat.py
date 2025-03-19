# app/domain/chat.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ChatMessage(BaseModel):
    """Model for a chat message"""
    id: str
    session_id: str
    user_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    is_fortune: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "is_fortune": self.is_fortune
        }
        
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result


class ChatSession(BaseModel):
    """Model for a chat session"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None
    messages: Optional[List[ChatMessage]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }
        
        if self.metadata:
            result["metadata"] = self.metadata
            
        if self.messages:
            result["messages"] = [msg.to_dict() for msg in self.messages]
            
        return result
        

class ChatHistoryRequest(BaseModel):
    """Request model for chat history API"""
    user_id: str
    session_id: Optional[str] = None
    limit: Optional[int] = 20
    offset: Optional[int] = 0
    active_only: Optional[bool] = True


class ChatHistoryResponse(BaseModel):
    """Response model for chat history API"""
    success: bool = True
    session: Optional[ChatSession] = None
    sessions: Optional[List[ChatSession]] = None
    messages: Optional[List[ChatMessage]] = None
    total_count: Optional[int] = None
    error: Optional[str] = None 