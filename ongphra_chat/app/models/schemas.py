from typing import List, Optional, Dict, Any, Literal, Union, Generic, TypeVar
from pydantic import BaseModel, Field, validator, create_model, root_validator
from datetime import datetime
import uuid

# Define response status
class ResponseStatus(BaseModel):
    success: bool = True
    message: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[int] = None

# Message models
class Message(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert the message to a dictionary for the OpenAI API."""
        return {
            "role": self.role,
            "content": self.content
        }

# Chat models
class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = False
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatMessageRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = False

class ToolCallInput(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolCallOutput(BaseModel):
    id: str
    type: str
    function: Dict[str, Any]

class ChatChoice(BaseModel):
    index: int
    message: Dict[str, Any]
    finish_reason: Optional[str] = None

class ChatCompletion(BaseModel):
    id: str
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Optional[Dict[str, int]] = None
    
    @root_validator(pre=True)
    def ensure_fields(cls, values):
        """Ensure all required fields are present"""
        if 'id' not in values:
            values['id'] = str(uuid.uuid4())
        if 'created' not in values:
            values['created'] = int(datetime.now().timestamp())
        if 'model' not in values:
            values['model'] = "default-model"
        return values

class ChatResponse(BaseModel):
    status: ResponseStatus = Field(default_factory=ResponseStatus)
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    response: ChatCompletion
    user_id: str
    session_id: str
    tool_result: Optional[Dict[str, Any]] = None
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

# Fortune models
class FortuneRequest(BaseModel):
    birthdate: str
    user_id: Optional[str] = None
    
    @validator('birthdate')
    def validate_birthdate(cls, v):
        try:
            # Check if birthdate is in YYYY-MM-DD format
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Birthdate must be in YYYY-MM-DD format")

class Base(BaseModel):
    name: str
    value: int

class FortuneBaseResponse(BaseModel):
    base1: Dict[str, int]
    base2: Dict[str, int]
    base3: Dict[str, int]
    base4: List[int]

class IndividualInterpretation(BaseModel):
    category: str
    meaning: str
    influence: str
    value: int
    heading: str
    detail: str

class CombinationInterpretation(BaseModel):
    category: str
    heading: str
    meaning: str
    influence: str

class FortuneResult(BaseModel):
    bases: Dict[str, Dict[str, int]]
    summary: Optional[str] = None
    combination_interpretations: Optional[List[Dict[str, Any]]] = None
    individual_interpretations: Optional[List[Dict[str, Any]]] = None

class FortuneResponse(BaseModel):
    status: ResponseStatus = Field(default_factory=ResponseStatus)
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    result: Union[FortuneResult, Dict[str, Any]]
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

# Generic API Response
T = TypeVar('T')
class ApiResponse(BaseModel, Generic[T]):
    status: ResponseStatus = Field(default_factory=ResponseStatus)
    data: Optional[T] = None
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

# Specialized FortuneExplanation Response
class FortuneExplanation(BaseModel):
    system_name: str
    description: str
    bases: Dict[str, str]
    interpretation: str

# Create specialized response models as needed
FortuneExplanationResponse = ApiResponse[FortuneExplanation]

# Streaming response models
class StreamingChunk(BaseModel):
    status: str  # "streaming", "complete", "error"
    message_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    content: str = ""
    complete_response: Optional[str] = None
    message: Optional[str] = None  # For error messages

class StreamingResponse(BaseModel):
    """FastAPI response model for streaming responses"""
    media_type: str = "text/event-stream"
    
    class Config:
        arbitrary_types_allowed = True

class StreamingChatRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    include_history: bool = True

class StreamingChatResponse(BaseModel):
    status: str
    message_id: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    complete_response: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        result = super().dict(*args, **kwargs)
        # Remove None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}