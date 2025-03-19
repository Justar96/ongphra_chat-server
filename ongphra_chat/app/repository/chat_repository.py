from typing import List, Dict, Optional, Any
import uuid
import json
from datetime import datetime

from app.repository.db_repository import DBRepository
from app.domain.chat import ChatSession, ChatMessage
from app.core.logging import get_logger


class ChatRepository:
    """Repository for chat sessions and messages"""
    
    def __init__(self):
        """Initialize the chat repository"""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Initialized ChatRepository")
    
    async def create_session(self, user_id: str, session_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new chat session
        
        Args:
            user_id: User identifier
            session_data: Optional additional session metadata
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Convert session data to JSON if provided
        metadata_json = None
        if session_data:
            metadata_json = json.dumps(session_data)
        
        # Insert new session
        query = """
            INSERT INTO chat_sessions (id, user_id, metadata)
            VALUES (%s, %s, %s)
        """
        
        await self._execute_query(query, session_id, user_id, metadata_json)
        self.logger.info(f"Created new chat session {session_id} for user {user_id}")
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get a chat session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            ChatSession object if found, None otherwise
        """
        query = """
            SELECT id, user_id, created_at, updated_at, is_active, metadata
            FROM chat_sessions
            WHERE id = %s
        """
        
        results = await self._execute_query(query, session_id)
        
        if not results:
            return None
            
        session_data = results[0]
        
        # Parse JSON data if available
        metadata_dict = None
        if session_data["metadata"]:
            try:
                metadata_dict = json.loads(session_data["metadata"])
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse session metadata JSON for session {session_id}")
        
        return ChatSession(
            id=session_data["id"],
            user_id=session_data["user_id"],
            created_at=session_data["created_at"],
            updated_at=session_data["updated_at"],
            is_active=session_data["is_active"],
            metadata=metadata_dict
        )
    
    async def get_user_sessions(self, user_id: str, limit: int = 10, active_only: bool = True) -> List[ChatSession]:
        """
        Get chat sessions for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            active_only: Whether to return only active sessions
            
        Returns:
            List of ChatSession objects
        """
        # Build query based on parameters
        query = """
            SELECT id, user_id, created_at, updated_at, is_active, metadata
            FROM chat_sessions
            WHERE user_id = %s
        """
        
        params = [user_id]
        
        if active_only:
            query += " AND is_active = TRUE"
        
        query += " ORDER BY updated_at DESC LIMIT %s"
        params.append(limit)
        
        results = await self._execute_query(query, *params)
        
        sessions = []
        for row in results:
            # Parse JSON data if available
            metadata_dict = None
            if row["metadata"]:
                try:
                    metadata_dict = json.loads(row["metadata"])
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse metadata JSON for session {row['id']}")
            
            sessions.append(ChatSession(
                id=row["id"],
                user_id=row["user_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                is_active=row["is_active"],
                metadata=metadata_dict
            ))
        
        return sessions
    
    async def update_session(self, session_id: str, is_active: Optional[bool] = None, session_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a chat session
        
        Args:
            session_id: Session identifier
            is_active: Optional new active status
            session_data: Optional new session metadata
            
        Returns:
            True if successful, False otherwise
        """
        # Build query based on what needs to be updated
        query_parts = []
        params = []
        
        if is_active is not None:
            query_parts.append("is_active = %s")
            params.append(is_active)
        
        if session_data is not None:
            query_parts.append("metadata = %s")
            params.append(json.dumps(session_data))
        
        # If nothing to update, return early
        if not query_parts:
            return True
        
        query = f"""
            UPDATE chat_sessions
            SET {", ".join(query_parts)}
            WHERE id = %s
        """
        
        params.append(session_id)
        
        await self._execute_query(query, *params)
        self.logger.info(f"Updated chat session {session_id}")
        
        return True
    
    async def add_message(self, session_id: str, user_id: str, role: str, content: str, is_fortune: bool = False, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a message to a chat session
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            role: Message role (user or assistant)
            content: Message content
            is_fortune: Whether this message contains a fortune reading
            metadata: Optional additional message metadata
            
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        
        # Convert metadata to JSON if provided
        metadata_json = None
        if metadata:
            metadata_json = json.dumps(metadata)
        
        # Insert new message
        query = """
            INSERT INTO chat_messages (id, session_id, user_id, role, content, is_fortune, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        await self._execute_query(query, message_id, session_id, user_id, role, content, is_fortune, metadata_json)
        
        # Update session's updated_at timestamp
        await self._execute_query(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            session_id
        )
        
        self.logger.info(f"Added {role} message to session {session_id}")
        
        return message_id
    
    async def get_session_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> List[ChatMessage]:
        """
        Get messages for a chat session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            offset: Offset for pagination
            
        Returns:
            List of ChatMessage objects
        """
        query = """
            SELECT id, session_id, user_id, role, content, timestamp, is_fortune, metadata
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY timestamp ASC
            LIMIT %s OFFSET %s
        """
        
        results = await self._execute_query(query, session_id, limit, offset)
        
        messages = []
        for row in results:
            # Parse JSON metadata if available
            metadata_dict = None
            if row["metadata"]:
                try:
                    metadata_dict = json.loads(row["metadata"])
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse metadata JSON for message {row['id']}")
            
            messages.append(ChatMessage(
                id=row["id"],
                session_id=row["session_id"],
                user_id=row["user_id"],
                role=row["role"],
                content=row["content"],
                timestamp=row["timestamp"],
                is_fortune=row["is_fortune"],
                metadata=metadata_dict
            ))
        
        return messages
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session and all its messages
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        # Delete the session (messages will be cascaded due to foreign key)
        query = "DELETE FROM chat_sessions WHERE id = %s"
        
        await self._execute_query(query, session_id)
        self.logger.info(f"Deleted chat session {session_id}")
        
        return True
    
    async def _execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a database query and return results"""
        from app.config.database import DatabaseManager
        
        try:
            async with await DatabaseManager.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    
                    # For SELECT queries, return results
                    if query.strip().upper().startswith("SELECT"):
                        columns = [col[0] for col in cursor.description]
                        results = await cursor.fetchall()
                        
                        # Convert to list of dictionaries
                        return [dict(zip(columns, row)) for row in results]
                    
                    # For other queries, commit and return empty list
                    await conn.commit()
                    return []
        except Exception as e:
            self.logger.error(f"Database error: {str(e)}", exc_info=True)
            raise e 