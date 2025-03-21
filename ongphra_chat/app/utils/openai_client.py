import json
import logging
import os
from typing import List, Dict, Any, AsyncGenerator, Optional, Generator
import httpx
from fastapi import HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncio
from sqlalchemy.orm import Session
import uuid
from sse_starlette.sse import EventSourceResponse

from app.config.settings import get_settings
from app.utils.fortune_tool import FORTUNE_TOOL_SCHEMA, calculate_7n9b_fortune
from app.config.database import get_db
from app.services.chat_service import ChatService
from app.models.schemas import StreamingChunk, StreamingChatRequest, StreamingChatResponse, ChatResponse
from openai import OpenAI, AsyncOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# System message for Thai chatbot
THAI_SYSTEM_MESSAGE = {
    "role": "system",
    "content": """คุณคือผู้ช่วยอัจฉริยะที่ชำนาญในการพูดคุยภาษาไทยและการทำนายดวงชะตาตามหลักเลข 7 ฐาน 9 ของไทย

เมื่อผู้ใช้ต้องการดูดวง:
1. สอบถามวันเดือนปีเกิด (รูปแบบ YYYY-MM-DD) อย่างสุภาพ
2. ใช้ฟังก์ชัน calculate_7n9b_fortune เพื่อคำนวณดวงชะตา
3. แปลผลการทำนายจากข้อมูลที่ได้รับจากฟังก์ชัน โดยให้ข้อมูล:
   - อธิบายว่าเลข 7 ฐาน 9 คืออะไร
   - เน้นจุดเด่นของฐานที่มีค่าสูง (5-7) และความหมาย
   - อธิบายความสัมพันธ์ระหว่างฐานที่น่าสนใจ
   - ให้คำแนะนำในการเสริมดวงที่เป็นประโยชน์

การแปลผลข้อมูลจากฟังก์ชัน:
- "bases": ข้อมูลตัวเลขแต่ละฐาน
- "individual_interpretations": คำอธิบายแต่ละเรื่อง
- "combination_interpretations": ความสัมพันธ์ระหว่างหมวดต่างๆ
- "summary": สรุปภาพรวมของดวง

การสนทนาทั่วไป:
- ตอบด้วยภาษาไทยที่สุภาพ เป็นกันเอง
- สามารถใช้อิโมจิเพื่อเพิ่มความเป็นมิตร
- ให้ข้อมูลที่ถูกต้อง และตรงประเด็น
- ส่งเสริมความรู้ที่ถูกต้องเกี่ยวกับศาสตร์ไทย"""
}

class OpenAIClient:
    def __init__(self, db: Session = None):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.api_url = f"{settings.openai_api_base}/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.client = httpx.AsyncClient(timeout=60.0)
        self.db = db
        self.chat_service = ChatService(db) if db else None
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
        self.system_prompt = settings.openai_system_prompt
        
    async def close(self):
        await self.client.aclose()
    
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session."""
        if self.chat_service and session_id:
            try:
                history = await self.chat_service.get_conversation_history_async(session_id)
                # Add system message if not present
                if not any(msg.get("role") == "system" for msg in history):
                    history = [THAI_SYSTEM_MESSAGE] + history
                return history
            except Exception as e:
                logger.error(f"Error getting conversation history: {str(e)}")
                # If there's an error, start with just the system message
                return [THAI_SYSTEM_MESSAGE]
        return [THAI_SYSTEM_MESSAGE]
    
    async def save_message(self, session_id: str, user_id: str, role: str, content: str) -> bool:
        """Save a message to the database."""
        if self.chat_service and session_id:
            try:
                await self.chat_service.add_message_async(session_id, user_id, role, content)
                return True
            except Exception as e:
                logger.error(f"Error saving message: {str(e)}")
        return False
    
    async def chat_completion(self, 
                               messages: List[Dict[str, str]], 
                               user_id: str = None,
                               session_id: Optional[str] = None,
                               stream: bool = False) -> Dict[str, Any]:
        """
        Get a completion from OpenAI API and persist the conversation.
        This method is async-compatible.
        """
        try:
            logger.info(f"Sending request to OpenAI: {messages}")
            
            # Get conversation history if session_id is provided
            if session_id:
                history = await self.get_conversation_history(session_id)
                
                # Add user message to history
                user_message = next((m for m in messages if m["role"] == "user"), None)
                if user_message:
                    # Save user message to database
                    await self.save_message(session_id, user_id, "user", user_message["content"])
                    
                    # Prepare messages with history
                    full_messages = history + messages
                else:
                    full_messages = messages
            else:
                full_messages = messages
            
            # Create async client request
            completion = await self.async_client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=stream
            )
            
            # If streaming, return the stream
            if stream:
                return completion
            
            # Process normal response
            assistant_message = completion.choices[0].message.content
            logger.info(f"Received response from OpenAI: {assistant_message}")
            
            # Save assistant message to database if session_id is provided
            if session_id and user_id:
                await self.save_message(session_id, user_id, "assistant", assistant_message)
            
            # Format response
            response = {
                "id": completion.id,
                "created": completion.created,
                "model": completion.model,
                "choices": [
                    {
                        "message": {"role": "assistant", "content": assistant_message},
                        "finish_reason": completion.choices[0].finish_reason
                    }
                ],
                "usage": {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    async def stream_chat_completion(self,
                                   messages: List[Dict[str, str]],
                                   user_id: str = None,
                                   session_id: Optional[str] = None) -> AsyncGenerator:
        """
        Stream a chat completion response from OpenAI and persist the completed conversation.
        This is an async-compatible streaming method.
        """
        try:
            logger.info(f"Sending streaming request to OpenAI: {messages}")
            
            # Get conversation history if session_id is provided
            if session_id:
                history = await self.get_conversation_history(session_id)
                
                # Add user message to history
                user_message = next((m for m in messages if m["role"] == "user"), None)
                if user_message:
                    # Save user message to database
                    await self.save_message(session_id, user_id, "user", user_message["content"])
                    
                    # Prepare messages with history
                    full_messages = history + messages
                else:
                    full_messages = messages
            else:
                full_messages = messages
            
            # Create streaming completion
            stream = await self.chat_completion(full_messages, user_id, session_id, stream=True)
            
            message_id = str(uuid.uuid4())
            full_response = ""
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield StreamingChunk(
                        status="streaming",
                        message_id=message_id,
                        user_id=user_id,
                        session_id=session_id,
                        content=content
                    )
            
            # Save the complete assistant message
            if session_id and user_id:
                await self.save_message(session_id, user_id, "assistant", full_response)
            
            yield StreamingChunk(
                status="complete",
                message_id=message_id,
                user_id=user_id,
                session_id=session_id,
                content="",
                complete_response=full_response
            )
            
        except Exception as e:
            logger.error(f"Error in streaming chat completion: {e}")
            yield StreamingChunk(
                status="error",
                message_id=str(uuid.uuid4()),
                user_id=user_id, 
                session_id=session_id,
                content="",
                error=str(e)
            )

    def build_messages(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """
        Build the message list for the OpenAI API with an optional history.
        """
        messages = []
        
        # Add system prompt if provided
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        # Add conversation history if provided
        if history:
            messages.extend(history)
        
        # Add current user message
        messages.append({"role": "user", "content": message})
        
        return messages

async def get_openai_client(db: Session = Depends(get_db)):
    """
    Get an instance of the OpenAI client.
    This function is an async context manager to properly clean up resources.
    """
    client = OpenAIClient(db)
    try:
        yield client
    finally:
        await client.close()