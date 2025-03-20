# app/services/response.py
from openai import AsyncOpenAI
from typing import Dict, Optional, List, Any, AsyncGenerator, Tuple, Union
import json
import asyncio
import time
import os
from datetime import datetime
import random

from app.core.exceptions import ResponseGenerationError
from app.config.settings import get_settings
from app.core.logging import get_logger
from app.services.session_service import get_session_manager
from app.services.reading_service import get_reading_service

class LRUCache:
    """
    Least Recently Used (LRU) cache implementation with size limiting and time-based expiration
    """
    
    def __init__(self, max_size=1000, ttl_seconds=3600):
        """
        Initialize the LRU Cache
        
        Args:
            max_size: Maximum number of items in cache
            ttl_seconds: Time-to-live in seconds for cache items
        """
        self.cache = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.access_order = []  # List to track access order
    
    def get(self, key):
        """Get item from cache, return None if missing or expired"""
        if key not in self.cache:
            return None
            
        # Check for expiration
        item = self.cache[key]
        current_time = time.time()
        if current_time - item["timestamp"] > self.ttl_seconds:
            # Remove expired item
            self._remove_item(key)
            return None
            
        # Update access order
        self._update_access(key)
        
        return item["value"]
    
    def set(self, key, value):
        """Add item to cache, managing size limits"""
        current_time = time.time()
        
        # If key exists, update it
        if key in self.cache:
            self.cache[key] = {
                "value": value,
                "timestamp": current_time
            }
            self._update_access(key)
            return
            
        # If cache is full, remove least recently used item
        if len(self.cache) >= self.max_size:
            self._remove_lru()
            
        # Add new item
        self.cache[key] = {
            "value": value,
            "timestamp": current_time
        }
        self.access_order.append(key)
    
    def _update_access(self, key):
        """Update access order for a key"""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def _remove_item(self, key):
        """Remove an item from cache and access order"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)
    
    def _remove_lru(self):
        """Remove least recently used item"""
        if not self.access_order:
            return
            
        lru_key = self.access_order[0]
        self._remove_item(lru_key)
    
    def clean_expired(self):
        """Clean up expired items"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time - item["timestamp"] > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self._remove_item(key)
            
    def size(self):
        """Get current cache size"""
        return len(self.cache)
    
    def clear(self):
        """Clear the cache"""
        self.cache = {}
        self.access_order = []

class ResponseService:
    """Service for generating responses using AI with conversation memory and streaming support"""
    
    def __init__(self):
        """Initialize the response service"""
        self.logger = get_logger(__name__)
        
        # Initialize settings
        settings = get_settings()
        self.openai_api_key = settings.openai_api_key
        self.default_model = settings.default_model
        self.cache_ttl = settings.cache_ttl
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # Initialize caches and memory
        self.response_cache = LRUCache(max_size=500, ttl_seconds=self.cache_ttl)
        self.conversation_memory = {}  # Memory for conversation history
        
        # Initialize retry settings
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        # Initialize prompt service
        from app.services.prompt import PromptService
        self.prompt_service = PromptService()
        
        self.logger.info(f"Initialized ResponseService with model {self.default_model}")
    
    def _get_cache_key(self, prompt: str, language: str, model_name: str) -> str:
        """Generate a cache key from prompt, language and model"""
        # Use first 100 chars of prompt to avoid excessive key size
        prompt_part = prompt[:100] if prompt else ""
        return f"{prompt_part}_{language}_{model_name}"
    
    def _should_use_cache(self, prompt: str) -> bool:
        """Determine if a prompt should use caching"""
        # Don't cache very short prompts
        if not prompt or len(prompt) < 20:
            return False
            
        # Skip cache for prompts that likely have changing context
        skip_phrases = [
            "current time", "current date", "right now", "today", "yesterday", "tomorrow",
            "เวลาปัจจุบัน", "วันที่ปัจจุบัน", "ตอนนี้", "วันนี้", "เมื่อวาน", "พรุ่งนี้"
        ]
        
        if any(phrase in prompt.lower() for phrase in skip_phrases):
            return False
            
        return True
        
    async def _create_completion_with_retry(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Any:
        """Create a chat completion with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if tools and tool_choice:
                    return await self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        tools=tools,
                        tool_choice=tool_choice,
                        temperature=0.7,
                        max_tokens=1000,
                        stream=stream
                    )
                else:
                    return await self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1000,
                        stream=stream
                    )
            except Exception as e:
                self.logger.warning(f"Attempt {attempt+1}/{self.max_retries} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed", exc_info=True)
                    raise ResponseGenerationError(f"Failed to generate response after {self.max_retries} attempts: {str(e)}")
    
    async def process_fortune_request(self, prompt: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a potential fortune reading request directly using the reading service
        
        Args:
            prompt: User's message/query
            user_id: User identifier for session tracking
            
        Returns:
            A structured response with fortune reading information
        """
        self.logger.info(f"Processing potential fortune request: '{prompt[:50]}...'")
        
        # Initialize result dictionary
        result = {
            "needs_birthdate": False,
            "is_fortune_request": False,
            "fortune_reading": None,
            "user_message": prompt,
            "extracted_birthdate": None,
            "error": None
        }
        
        try:
            # Get required services
            session_manager = get_session_manager()
            reading_service = await get_reading_service()
            
            # 1. Determine if this is a fortune request (moved from fortune_tool.py)
            from app.services.ai_topic_service import get_ai_topic_service
            ai_topic_service = get_ai_topic_service()
            
            # Check for fortune keywords (simplified from the original)
            FORTUNE_KEYWORDS = [
                'ดวง', 'ดูดวง', 'ทำนาย', 'โหราศาสตร์', 'ชะตา', 'ไพ่ยิปซี', 'ราศี', 
                'fortune', 'horoscope', 'predict', 'future', 'astrology', 'tarot',
                'ฐานเกิด', 'เลขฐาน', 'วันเกิด'
            ]
            
            # Simple detection - for comprehensive detection implement the multi-method approach from fortune_tool
            is_fortune_request = any(keyword in prompt.lower() for keyword in FORTUNE_KEYWORDS)
            
            # Also check with the AI topic service if available
            try:
                if ai_topic_service and not is_fortune_request:
                    topic_result = await ai_topic_service.detect_topic(prompt)
                    if topic_result and topic_result.primary_topic in ["ทั่วไป", "โชคลาภ", "อนาคต"]:
                        is_fortune_request = True
            except Exception:
                pass
                
            result["is_fortune_request"] = is_fortune_request
            
            if not is_fortune_request:
                return result
                
            # 2. Extract birth date or get from session
            birth_date = None 
            thai_day = None
            
            # Try to extract date from message (simplified - implement full extraction from fortune_tool if needed)
            DATE_PATTERN = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'  # DD/MM/YYYY pattern
            import re
            date_match = re.search(DATE_PATTERN, prompt)
            
            if date_match:
                try:
                    day, month, year = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        birth_date = datetime(year, month, day)
                        result["extracted_birthdate"] = birth_date.strftime("%Y-%m-%d")
                        session_manager.save_birth_info(user_id, birth_date, thai_day)
                except (ValueError, IndexError):
                    pass
            
            # Check for birth info in session if not extracted from message
            if not birth_date and user_id:
                birth_info = session_manager.get_birth_info(user_id)
                if birth_info:
                    try:
                        birth_date = datetime.strptime(birth_info["birth_date"], "%Y-%m-%d")
                        thai_day = birth_info["thai_day"]
                    except (ValueError, KeyError):
                        pass
                        
            # If we don't have birth date, indicate that we need it
            if not birth_date:
                result["needs_birthdate"] = True
                return result
                
            # 3. Generate fortune reading using reading service
            try:
                reading = await reading_service.get_fortune_reading(
                    birth_date=birth_date,
                    thai_day=thai_day,
                    user_question=prompt,
                    user_id=user_id
                )
                
                # Add topic information if available
                if reading and ai_topic_service:
                    try:
                        topic_result = await ai_topic_service.detect_topic(prompt)
                        if topic_result:
                            reading.topic = topic_result.primary_topic
                            reading.confidence = topic_result.confidence
                    except Exception:
                        pass
                
                result["fortune_reading"] = reading.dict() if reading else None
                
            except Exception as e:
                self.logger.error(f"Error getting fortune reading: {str(e)}", exc_info=True)
                result["error"] = str(e)
                
                # Implement fallback logic if needed (simplified from fortune_tool.py)
                # For brevity, I've omitted the fallback logic, but it can be added if necessary
            
            return result
            
        except Exception as e:
            self.logger.error(f"Unexpected error in fortune processing: {str(e)}", exc_info=True)
            result["error"] = str(e)
            return result
    
    async def generate_response(
        self,
        prompt: str,
        language: str = "thai",
        has_birth_info: bool = False,
        user_id: Optional[str] = None,
        stream: bool = False,
        process_fortune: bool = True  # Parameter to control fortune processing
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate a response to a user prompt using OpenAI API
        
        Args:
            prompt: User's prompt or question
            language: Response language (thai or english)
            has_birth_info: Whether the user has provided birth information
            user_id: Unique identifier for the user for session tracking
            stream: Whether to stream the response
            process_fortune: Whether to check for and process fortune requests
            
        Returns:
            Generated response as string or async generator for streaming
        """
        try:
            # Save user message to session if user_id is provided
            if user_id:
                session_manager = get_session_manager()
                session_manager.save_conversation_message(user_id, "user", prompt)
                self.logger.debug(f"Saved user message to session for user {user_id}")
            
            # Process fortune detection first if enabled (use our direct method)
            fortune_result = None
            if process_fortune:
                try:
                    fortune_result = await self.process_fortune_request(prompt, user_id)
                    self.logger.debug(f"Fortune detection result: {fortune_result['is_fortune_request']}")
                    
                    if fortune_result["is_fortune_request"]:
                        self.logger.info("Detected fortune request, processing with fortune tool")
                        
                        if fortune_result["needs_birthdate"]:
                            # User needs to provide birth date
                            response_text = self._get_birthdate_request_message(language)
                            
                            # Save assistant response to session
                            if user_id:
                                session_manager.save_conversation_message(user_id, "assistant", response_text)
                            
                            # Return as string or stream based on request
                            if stream:
                                return self._stream_text(response_text)
                            else:
                                return response_text
                        
                        elif fortune_result["fortune_reading"]:
                            # Process the fortune reading
                            reading = fortune_result["fortune_reading"]
                            
                            # Format the response
                            response_text = self._format_fortune_reading(reading, language)
                            
                            # Save assistant response to session
                            if user_id:
                                session_manager.save_conversation_message(user_id, "assistant", response_text)
                            
                            # Save reading data to session context for tracking
                            if user_id:
                                session_manager.save_context_data(user_id, "last_reading", reading)
                            
                            # Return as string or stream based on request
                            if stream:
                                return self._stream_text(response_text)
                            else:
                                return response_text
                
                except Exception as fortune_error:
                    # Log the error but continue with normal response generation
                    self.logger.error(f"Error processing fortune request: {str(fortune_error)}", exc_info=True)
            
            # If we reach here, either:
            # 1. Fortune processing is disabled
            # 2. It's not a fortune request
            # 3. Fortune processing failed
            # Continue with normal response generation
            
            # Generate appropriate system prompt
            if has_birth_info:
                system_prompt = self.prompt_service.generate_system_prompt(language)
            else:
                system_prompt = self.prompt_service.generate_general_system_prompt(language)
            
            # Build conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Get conversation history from session if user_id is provided
            if user_id:
                session_manager = get_session_manager()
                history = session_manager.get_conversation_history(user_id)
                
                # Add a limited number of most recent messages
                if history:
                    # Limit to max_conversation_turns or default
                    max_turns = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))
                    recent_history = history[-max_turns*2:] if len(history) > max_turns*2 else history
                    messages.extend(recent_history)
                    self.logger.debug(f"Added {len(recent_history)} messages from session history")
            
            # Add current user message if not already in session
            if not user_id or (user_id and messages[-1]["role"] != "user"):
                messages.append({"role": "user", "content": prompt})
            
            # Check if we have this response cached
            cache_key = self._get_cache_key(prompt, language, self.default_model)
            cached_response = self._get_cached_response(cache_key) if not stream else None
            
            if cached_response:
                self.logger.info("Using cached response")
                # Save assistant response to session if user_id is provided
                if user_id:
                    session_manager = get_session_manager()
                    session_manager.save_conversation_message(user_id, "assistant", cached_response)
                return cached_response
            
            # Stream the response if requested
            if stream:
                return self._generate_streaming_response(messages, user_id)
            
            # Generate the response
            response = await self._generate_openai_response(messages)
            
            # Cache the response
            self._cache_response(cache_key, response)
            
            # Save assistant response to session if user_id is provided
            if user_id:
                session_manager = get_session_manager()
                session_manager.save_conversation_message(user_id, "assistant", response)
            
            return response
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return "ขออภัย เกิดข้อผิดพลาดในการตอบคำถาม โปรดลองอีกครั้งในภายหลัง" if language.lower() == "thai" else "Sorry, an error occurred while generating the response. Please try again later."
        
    def _get_birthdate_request_message(self, language: str = "thai") -> str:
        """
        Get a formatted request for birthdate message in the specified language
        
        Args:
            language: The language to format the message in (thai or english)
            
        Returns:
            Formatted message requesting birthdate
        """
        if language.lower() == "english":
            return (
                "To provide you with a fortune reading, I need to know your birth date. "
                "Please provide your birth date in the format DD/MM/YYYY. "
                "For example, if you were born on January 5, 1990, please type '5/1/1990'."
            )
        else:
            return (
                "เพื่อให้ฉันสามารถดูดวงให้คุณได้ ฉันต้องการทราบวันเกิดของคุณ "
                "กรุณาให้วันเกิดของคุณในรูปแบบ วัน/เดือน/ปี "
                "ตัวอย่างเช่น หากคุณเกิดวันที่ 5 มกราคม 2533 กรุณาพิมพ์ '5/1/2533'"
            )
            
    def _format_fortune_reading(self, reading: Dict[str, Any], language: str = "thai") -> str:
        """
        Format a fortune reading result into a readable response with proper Thai text formatting
        
        Args:
            reading: The fortune reading data
            language: The language to format the response in (thai or english)
            
        Returns:
            Formatted fortune reading response
        """
        if not reading:
            return self._get_fortune_error_message(language)
            
        try:
            # Extract reading parts
            heading = reading.get("heading", "")
            meaning = reading.get("meaning", "")
            influence_type = reading.get("influence_type", "")
            birth_date = reading.get("birth_date", "")
            thai_day = reading.get("thai_day", "")
            question = reading.get("question", "")
            
            # Format response based on language
            if language.lower() == "english":
                response = "🔮 **Fortune Reading** 🔮\n\n"
                
                if heading:
                    response += f"**Topic**: {heading}\n\n"
                    
                if birth_date or thai_day:
                    response += "**Birth Information**:\n"
                    if birth_date:
                        response += f"Date: {birth_date}\n"
                    if thai_day:
                        response += f"Day: {thai_day}\n"
                    response += "\n"
                    
                if meaning:
                    response += f"**Reading**:\n{meaning}\n\n"
                    
                if influence_type:
                    response += f"**Influence**: {influence_type}"
            else:
                response = "🔮 **การดูดวง** 🔮\n\n"
                
                if heading:
                    response += f"**หัวข้อ**: {heading}\n\n"
                    
                if birth_date or thai_day:
                    response += "**ข้อมูลวันเกิด**:\n"
                    if birth_date:
                        response += f"วันที่: {birth_date}\n"
                    if thai_day:
                        response += f"วัน: {thai_day}\n"
                    response += "\n"
                    
                if meaning:
                    # Split meaning into paragraphs and format
                    paragraphs = meaning.split("\n\n")
                    formatted_paragraphs = []
                    for p in paragraphs:
                        # Ensure proper line breaks for Thai text
                        lines = [line.strip() for line in p.split("\n")]
                        formatted_p = "\n".join(line for line in lines if line)
                        if formatted_p:
                            formatted_paragraphs.append(formatted_p)
                    
                    response += "**คำทำนาย**:\n" + "\n\n".join(formatted_paragraphs) + "\n\n"
                    
                if influence_type:
                    response += f"**ลักษณะ**: {influence_type}"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error formatting fortune reading: {str(e)}", exc_info=True)
            return self._get_fortune_error_message(language)
            
    def _get_fortune_error_message(self, language: str = "thai") -> str:
        """
        Get a formatted error message for fortune reading failures
        
        Args:
            language: The language for the error message
            
        Returns:
            Formatted error message
        """
        if language.lower() == "english":
            return (
                "I apologize, but I'm having trouble generating your fortune reading at the moment. "
                "This could be due to a technical issue. "
                "Please try again later or ask me a different question."
            )
        else:
            return (
                "ขออภัย ฉันมีปัญหาในการดูดวงให้คุณในขณะนี้ "
                "อาจเกิดจากปัญหาทางเทคนิค "
                "โปรดลองอีกครั้งในภายหลัง หรือถามคำถามอื่น"
            )
    
    async def _stream_text(self, text: str) -> AsyncGenerator[str, None]:
        """
        Create an async generator for streaming text
        
        Args:
            text: The text to stream
            
        Yields:
            Text chunks for streaming
        """
        # Simple implementation - divide the text into smaller chunks for streaming
        chunk_size = 20  # Characters per chunk, adjust as needed
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            yield chunk
            # Small delay to simulate typing
            await asyncio.sleep(0.05)
    
    async def _generate_openai_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response using OpenAI API
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Generated response
        """
        try:
            self.logger.debug(f"Generating response with {len(messages)} messages")
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            response_text = response.choices[0].message.content.strip()
            self.logger.debug(f"Generated response with {len(response_text)} characters")
            return response_text
        except Exception as e:
            self.logger.error(f"Error in OpenAI API call: {str(e)}", exc_info=True)
            raise
    
    async def _generate_streaming_response(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using OpenAI API
        
        Args:
            messages: List of message dictionaries with role and content
            user_id: User identifier for session tracking
            
        Yields:
            Chunks of the generated response
        """
        try:
            self.logger.debug(f"Generating streaming response with {len(messages)} messages")
            
            # Initialize the OpenAI streaming response
            stream = await self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                stream=True
            )
            
            # Collect the full response for saving to session
            full_response = ""
            
            # Stream the response chunks
            async for chunk in stream:
                if hasattr(chunk.choices[0], "delta") and hasattr(chunk.choices[0].delta, "content"):
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        yield content
            
            # Save the full response to session if user_id is provided
            if user_id and full_response:
                # Save to conversation memory
                self.conversation_memory[user_id] = self.conversation_memory.get(user_id, [])
                self.conversation_memory[user_id].append({
                    "role": "assistant",
                    "content": full_response
                })
                
                # Save to session
                session_manager = get_session_manager()
                session_manager.save_conversation_message(user_id, "assistant", full_response)
                self.logger.debug(f"Saved assistant streaming response to session for user {user_id}")
            
            # Send the end of stream marker
            yield "[DONE]"
        except Exception as e:
            self.logger.error(f"Error in streaming response: {str(e)}", exc_info=True)
            yield f"ขออภัย เกิดข้อผิดพลาดในการสตรีมข้อความ: {str(e)}"
            yield "[DONE]"
    
    def clear_user_conversation(self, user_id: str) -> bool:
        """Clear conversation history for a user"""
        # Clear from old conversation memory
        if user_id in self.conversation_memory:
            del self.conversation_memory[user_id]
            self.logger.info(f"Cleared conversation history for user {user_id} from memory")
        
        # Also clear from session manager
        session_manager = get_session_manager()
        session_cleared = session_manager.clear_session(user_id)
        
        self.logger.info(f"Cleared session for user {user_id}: {session_cleared}")
        return True
    
    def clear_cache(self) -> int:
        """Clear the response cache and return number of items cleared"""
        count = len(self.response_cache)
        self.response_cache.clear()
        self.logger.info(f"Cleared response cache ({count} items)")
        return count

    def _cache_response(self, cache_key: str, response: str) -> None:
        """Cache a response with timestamp"""
        self.response_cache.set(cache_key, response)
        
        # Clean expired items occasionally (1% chance)
        if random.random() < 0.01:
            self.response_cache.clean_expired()

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get a cached response if it exists and is not expired"""
        return self.response_cache.get(cache_key)