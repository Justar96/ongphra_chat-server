from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta
import json

from app.core.logging import get_logger


class SessionManager:
    """Service for managing user session data and conversation history"""
    
    def __init__(self, max_sessions: int = 1000, session_ttl: int = 86400):
        """
        Initialize the session manager
        
        Args:
            max_sessions: Maximum number of sessions to store in memory
            session_ttl: Time to live for sessions in seconds (default 24 hours)
        """
        self.logger = get_logger(__name__)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_sessions = max_sessions
        self.session_ttl = session_ttl
        self.logger.info(f"Initialized SessionManager with max_sessions={max_sessions}, ttl={session_ttl}s")
    
    def get_session(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user session by ID, creating a new one if it doesn't exist
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            The user's session data
        """
        # Clean up expired sessions occasionally
        if len(self.sessions) > self.max_sessions * 0.9:
            self._cleanup_expired_sessions()
        
        # Get existing session or create a new one
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "created_at": time.time(),
                "last_updated": time.time(),
                "conversation_history": [],
                "birth_info": None,
                "thai_day": None,
                "previous_topics": [],
                "context": {}
            }
            self.logger.info(f"Created new session for user {user_id}")
        else:
            # Update last_updated timestamp
            self.sessions[user_id]["last_updated"] = time.time()
        
        return self.sessions[user_id]
    
    def save_conversation_message(
        self, 
        user_id: str, 
        role: str, 
        content: str, 
        max_history: int = 20
    ) -> None:
        """
        Save a conversation message to the user's session
        
        Args:
            user_id: Unique identifier for the user
            role: Message role (user or assistant)
            content: Message content
            max_history: Maximum number of messages to keep in history
        """
        session = self.get_session(user_id)
        
        # Add message to history
        session["conversation_history"].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # Trim history if needed
        if len(session["conversation_history"]) > max_history:
            session["conversation_history"] = session["conversation_history"][-max_history:]
            
        self.logger.debug(f"Saved {role} message for user {user_id}, history size: {len(session['conversation_history'])}")
    
    def get_conversation_history(
        self, 
        user_id: str, 
        max_messages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user
        
        Args:
            user_id: Unique identifier for the user
            max_messages: Maximum number of messages to return
            
        Returns:
            List of conversation messages
        """
        session = self.get_session(user_id)
        history = session["conversation_history"]
        
        # Return at most max_messages
        return history[-max_messages:] if history else []
    
    def save_birth_info(self, user_id: str, birth_date: datetime, thai_day: str) -> None:
        """
        Save birth information to the user's session
        
        Args:
            user_id: Unique identifier for the user
            birth_date: User's birth date
            thai_day: Thai day of birth
        """
        session = self.get_session(user_id)
        session["birth_info"] = birth_date.strftime("%Y-%m-%d")
        session["thai_day"] = thai_day
        self.logger.info(f"Saved birth info for user {user_id}: {birth_date.strftime('%Y-%m-%d')}, {thai_day}")
    
    def get_birth_info(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        Get birth information from the user's session
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dictionary with birth_date and thai_day, or None if not found
        """
        session = self.get_session(user_id)
        if session["birth_info"] and session["thai_day"]:
            return {
                "birth_date": session["birth_info"],
                "thai_day": session["thai_day"]
            }
        return None
    
    def save_topic(self, user_id: str, topic: str) -> None:
        """
        Save a query topic to the user's session
        
        Args:
            user_id: Unique identifier for the user
            topic: Topic of the user's question
        """
        session = self.get_session(user_id)
        if "previous_topics" not in session:
            session["previous_topics"] = []
        
        # Add topic if it's not already the most recent one
        if not session["previous_topics"] or session["previous_topics"][-1] != topic:
            session["previous_topics"].append(topic)
            
            # Keep only the last 5 topics
            if len(session["previous_topics"]) > 5:
                session["previous_topics"] = session["previous_topics"][-5:]
                
        self.logger.debug(f"Saved topic '{topic}' for user {user_id}")
    
    def get_recent_topics(self, user_id: str, max_topics: int = 3) -> List[str]:
        """
        Get recent topics from the user's session
        
        Args:
            user_id: Unique identifier for the user
            max_topics: Maximum number of topics to return
            
        Returns:
            List of recent topics
        """
        session = self.get_session(user_id)
        topics = session.get("previous_topics", [])
        
        # Return at most max_topics, most recent first
        return topics[-max_topics:] if topics else []
    
    def save_context_data(self, user_id: str, key: str, value: Any) -> None:
        """
        Save arbitrary context data to the user's session
        
        Args:
            user_id: Unique identifier for the user
            key: Context data key
            value: Context data value (must be JSON serializable)
        """
        session = self.get_session(user_id)
        if "context" not in session:
            session["context"] = {}
            
        session["context"][key] = value
        self.logger.debug(f"Saved context data '{key}' for user {user_id}")
    
    def get_context_data(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Get context data from the user's session
        
        Args:
            user_id: Unique identifier for the user
            key: Context data key
            default: Default value if key not found
            
        Returns:
            Context data value or default
        """
        session = self.get_session(user_id)
        context = session.get("context", {})
        return context.get(key, default)
    
    def clear_session(self, user_id: str) -> bool:
        """
        Clear a user's session
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            True if session was cleared, False if not found
        """
        if user_id in self.sessions:
            del self.sessions[user_id]
            self.logger.info(f"Cleared session for user {user_id}")
            return True
        return False
    
    def _cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions
        
        Returns:
            Number of sessions removed
        """
        now = time.time()
        expired_user_ids = [
            user_id for user_id, session in self.sessions.items()
            if now - session["last_updated"] > self.session_ttl
        ]
        
        for user_id in expired_user_ids:
            del self.sessions[user_id]
            
        if expired_user_ids:
            self.logger.info(f"Cleaned up {len(expired_user_ids)} expired sessions")
            
        return len(expired_user_ids)
    
    def export_session(self, user_id: str) -> Optional[str]:
        """
        Export a user's session as JSON
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            JSON string of session data or None if not found
        """
        if user_id in self.sessions:
            try:
                return json.dumps(self.sessions[user_id])
            except Exception as e:
                self.logger.error(f"Error exporting session for user {user_id}: {str(e)}")
                return None
        return None
    
    def import_session(self, user_id: str, session_data: str) -> bool:
        """
        Import a user's session from JSON
        
        Args:
            user_id: Unique identifier for the user
            session_data: JSON string of session data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.sessions[user_id] = json.loads(session_data)
            self.sessions[user_id]["last_updated"] = time.time()
            self.logger.info(f"Imported session for user {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error importing session for user {user_id}: {str(e)}")
            return False


# Singleton instance for global access
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get singleton instance of SessionManager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager 