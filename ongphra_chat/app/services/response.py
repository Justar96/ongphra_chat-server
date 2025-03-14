# app/services/response.py
from openai import AsyncOpenAI
from typing import Dict, Optional, List, Any
import json

from app.core.exceptions import ResponseGenerationError
from app.config.settings import get_settings

class ResponseService:
    """Service for generating responses using AI"""
    
    def __init__(self):
        """Initialize the response service with API key from settings"""
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.default_model = settings.default_model
    
    async def generate_response(
        self, 
        prompt: str, 
        language: str = "thai", 
        has_birth_info: bool = True,
        model: Optional[str] = None
    ) -> str:
        """
        Generate a fortune telling response using OpenAI
        
        Args:
            prompt: The user prompt with all context
            language: Response language
            has_birth_info: Whether birth info is provided
            model: Optional model to use (defaults to settings)
            
        Returns:
            Generated fortune telling response
        """
        try:
            # Use provided model or fall back to default
            model_name = model or self.default_model
            
            # Generate system prompt based on whether we have birth info
            from app.services.prompt import PromptService
            prompt_service = PromptService()
            
            if has_birth_info:
                system_prompt = prompt_service.generate_system_prompt(language)
            else:
                system_prompt = prompt_service.generate_general_system_prompt(language)
            
            # Try using function calling first
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
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    tools=tools,
                    tool_choice={"type": "function", "function": {"name": "generate_fortune"}},
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Extract the fortune from the function call
                tool_call = response.choices[0].message.tool_calls[0]
                fortune_data = json.loads(tool_call.function.arguments)
                
                return fortune_data["fortune"]
                
            except Exception as function_error:
                # If function calling fails, fall back to regular completion
                print(f"Function calling failed: {str(function_error)}. Falling back to regular completion.")
                
                fallback_response = await self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                return fallback_response.choices[0].message.content
            
        except Exception as e:
            error_msg = f"Error generating AI response: {str(e)}"
            print(error_msg)
            
            # Return a fallback message instead of raising an exception
            if language.lower() == "english":
                return "I apologize, but I'm unable to provide a reading at this moment. Please try again later."
            else:
                return "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"