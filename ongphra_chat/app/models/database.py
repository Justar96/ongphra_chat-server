from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import datetime
import uuid

from app.config.database import Base

class ChatSession(Base):
    """Model for chat sessions."""
    __tablename__ = "chat_sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    meta_data = Column(Text, nullable=True)
    
    # Define relationship to messages - this is the main relationship
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Add relationship to fortune calculations
    fortune_calculations = relationship("FortuneCalculation", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.get_title(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }
    
    def get_title(self):
        """Get the title from metadata or return a default title."""
        if self.meta_data:
            try:
                import json
                metadata = json.loads(self.meta_data)
                return metadata.get("title", f"Chat {self.created_at.strftime('%Y-%m-%d %H:%M')}")
            except:
                pass
        return f"Chat {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class ChatMessage(Base):
    """Model for chat messages."""
    __tablename__ = "chat_messages"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    content = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_fortune = Column(Boolean, default=False)
    meta_data = Column(Text, nullable=True)
    
    # Define relationship back to session - this is the secondary relationship
    session = relationship("ChatSession", back_populates="messages")
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sequence": self.get_sequence(),
            "is_fortune": self.is_fortune
        }
    
    def get_sequence(self):
        """Get the sequence from metadata or return a default sequence."""
        if self.meta_data:
            try:
                import json
                metadata = json.loads(self.meta_data)
                return metadata.get("sequence", 1)
            except:
                pass
        return 1
    
    def to_openai_message(self):
        """Convert to OpenAI message format."""
        return {
            "role": self.role,
            "content": self.content
        }

class FortuneCalculation(Base):
    """Model for storing fortune calculation results."""
    __tablename__ = "fortune_calculations"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    birthdate = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Store the base values individually for quick access
    base1 = Column(Text, nullable=True)  # JSON string of base1 categories and values
    base2 = Column(Text, nullable=True)  # JSON string of base2 categories and values
    base3 = Column(Text, nullable=True)  # JSON string of base3 categories and values
    
    # Store the full calculation result
    result_json = Column(Text, nullable=True)  # Complete fortune calculation as JSON string
    
    # Define relationship back to session
    session = relationship("ChatSession", back_populates="fortune_calculations")
    
    def to_dict(self):
        """Convert fortune calculation to dictionary."""
        import json
        
        # Parse JSON strings to dictionaries
        base1_dict = json.loads(self.base1) if self.base1 else {}
        base2_dict = json.loads(self.base2) if self.base2 else {}
        base3_dict = json.loads(self.base3) if self.base3 else {}
        full_result = json.loads(self.result_json) if self.result_json else {}
        
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "birthdate": self.birthdate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "base1": base1_dict,
            "base2": base2_dict,
            "base3": base3_dict,
            "full_result": full_result
        }
    
    def get_category_value(self, category_name):
        """Get the value for a specific category."""
        import json
        
        # Check each base for the category
        for base_str in [self.base1, self.base2, self.base3]:
            if not base_str:
                continue
                
            base_dict = json.loads(base_str)
            if category_name in base_dict:
                return base_dict[category_name]
                
        return None

# Database connection
def get_engine(connection_string):
    """Create database engine."""
    return create_engine(connection_string)

def init_db(engine):
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

def get_db_session(engine):
    """Create a database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal() 