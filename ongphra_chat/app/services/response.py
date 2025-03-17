# app/services/response.py
from openai import AsyncOpenAI
from typing import Dict, Optional, List, Any, AsyncGenerator, Tuple, Union
import json
import asyncio
import time
import os

from app.core.exceptions import ResponseGenerationError
from app.config.settings import get_settings
from app.core.logging import get_logger
from app.services.session_service import get_session_manager

class ResponseService:
    """Service for generating responses using AI with conversation memory and streaming support"""
    
    def __init__(self):
        """Initialize the response service"""
        self.logger = get_logger(__name__)
        
        # Initialize settings
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # Initialize caches and memory
        self.response_cache = {}  # Cache for responses
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
    
    async def generate_response(
        self,
        prompt: str,
        language: str = "thai",
        has_birth_info: bool = False,
        user_id: Optional[str] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate a response to a user prompt using OpenAI API
        
        Args:
            prompt: User's prompt or question
            language: Response language (thai or english)
            has_birth_info: Whether the user has provided birth information
            user_id: Unique identifier for the user for session tracking
            stream: Whether to stream the response
            
        Returns:
            Generated response as string or async generator for streaming
        """
        try:
            # Save user message to session if user_id is provided
            if user_id:
                session_manager = get_session_manager()
                session_manager.save_conversation_message(user_id, "user", prompt)
                self.logger.debug(f"Saved user message to session for user {user_id}")
            
            # Generate appropriate system prompt
            if has_birth_info:
                system_prompt = self.prompt_service.generate_general_system_prompt(language)
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
                        yield f"data: {content}\n\n"
            
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
            yield "data: [DONE]\n\n"
        except Exception as e:
            self.logger.error(f"Error in streaming response: {str(e)}", exc_info=True)
            yield f"data: ขออภัย เกิดข้อผิดพลาดในการสตรีมข้อความ: {str(e)}\n\n"
            yield "data: [DONE]\n\n"
    
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
        self.response_cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        # Limit cache size
        if len(self.response_cache) > 100:
            # Find and remove oldest entry
            oldest_key = min(
                self.response_cache.keys(),
                key=lambda k: self.response_cache[k]["timestamp"]
            )
            del self.response_cache[oldest_key]

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get a cached response if it exists and is not expired"""
        if cache_key in self.response_cache:
            cache_entry = self.response_cache[cache_key]
            # Check if cache entry is still valid
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["response"]
        return None