# app/services/response.py
from openai import AsyncOpenAI
from typing import Dict, Optional, List, Any, AsyncGenerator
import json
import asyncio

from app.core.exceptions import ResponseGenerationError
from app.config.settings import get_settings

class ResponseService:
    """Service for generating responses using AI with conversation memory and streaming support"""
    
    def __init__(self):
        """Initialize the response service with API key from settings"""
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.default_model = settings.default_model
        # Initialize conversation memory - will store per-user conversations
        self.conversation_memory = {}
    
    async def generate_response(
        self, 
        prompt: str, 
        language: str = "thai", 
        has_birth_info: bool = True,
        model: Optional[str] = None,
        user_id: str = "default_user",
        max_history: int = 10,
        stream: bool = False
    ) -> str:
        """
        Generate a fortune telling response using OpenAI
        
        Args:
            prompt: The user prompt with all context
            language: Response language (thai or english)
            has_birth_info: Whether birth info is provided
            model: Optional model to use (defaults to settings)
            user_id: User identifier for conversation tracking
            max_history: Maximum number of conversation turns to remember
            stream: Whether to return a streaming response
            
        Returns:
            Generated fortune telling response (or streaming iterator if stream=True)
        """
        # Use provided model or fall back to default
        model_name = model or self.default_model
        
        # Generate system prompt based on whether we have birth info
        from app.services.prompt import PromptService
        prompt_service = PromptService()
        
        if has_birth_info:
            system_prompt = prompt_service.generate_system_prompt(language)
        else:
            system_prompt = prompt_service.generate_general_system_prompt(language)
        
        # Initialize conversation for this user if it doesn't exist
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        
        # Add user's current message to history
        self.conversation_memory[user_id].append({"role": "user", "content": prompt})
        
        # Prepare messages with conversation history
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add conversation history (limited to max_history)
        history = self.conversation_memory[user_id][-max_history:]
        messages.extend(history)
        
        try:
            if stream:
                return await self._generate_streaming_response(
                    messages, model_name, user_id, language, max_history
                )
            else:
                return await self._generate_standard_response(
                    messages, model_name, user_id, language, max_history
                )
        except Exception as e:
            # Handle any errors
            error_msg = f"Error generating AI response: {str(e)}"
            print(error_msg)
            
            # Return a fallback message instead of raising an exception
            if language.lower() == "english":
                return "I apologize, but I'm unable to provide a reading at this moment. Please try again later."
            else:
                return "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
    
    async def _generate_standard_response(
        self, 
        messages: List[Dict[str, str]], 
        model_name: str,
        user_id: str,
        language: str,
        max_history: int = 10
    ) -> str:
        """Generate a standard (non-streaming) response"""
        # Try using function calling first for structured fortune response
        try:
            # Define the fortune telling function
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "generate_fortune",
                        "description": "Generate a fortune telling response based on the user's question and birth information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "fortune": {
                                    "type": "string",
                                    "description": "The fortune telling response"
                                }
                            },
                            "required": ["fortune"],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                }
            ]
            
            # Call OpenAI API with function calling
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "generate_fortune"}},
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract the fortune from the function call
            tool_call = response.choices[0].message.tool_calls[0]
            fortune_data = json.loads(tool_call.function.arguments)
            fortune_text = fortune_data["fortune"]
            
        except Exception as function_error:
            # If function calling fails, fall back to regular completion
            print(f"Function calling failed: {str(function_error)}. Falling back to regular completion.")
            
            fallback_response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            fortune_text = fallback_response.choices[0].message.content
        
        # Add assistant's response to conversation history
        self.conversation_memory[user_id].append({"role": "assistant", "content": fortune_text})
        
        # Trim history if needed
        if len(self.conversation_memory[user_id]) > max_history * 2:  # *2 to account for both user and assistant messages
            self.conversation_memory[user_id] = self.conversation_memory[user_id][-max_history*2:]
        
        return fortune_text
    
    async def _generate_streaming_response(
        self, 
        messages: List[Dict[str, str]], 
        model_name: str,
        user_id: str,
        language: str,
        max_history: int = 10
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response"""
        try:
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                stream=True
            )
            
            # Initialize variables to collect the full response
            full_response = ""
            
            # Stream the response back
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # After streaming is complete, save to conversation history
            self.conversation_memory[user_id].append({"role": "assistant", "content": full_response})
            
            # Trim history if needed
            if len(self.conversation_memory[user_id]) > max_history * 2:
                self.conversation_memory[user_id] = self.conversation_memory[user_id][-max_history*2:]
                
        except Exception as e:
            # Handle any errors during streaming
            error_msg = f"Error in streaming response: {str(e)}"
            print(error_msg)
            
            # Yield a fallback message
            if language.lower() == "english":
                yield "I apologize, but I'm unable to provide a reading at this moment. Please try again later."
            else:
                yield "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"