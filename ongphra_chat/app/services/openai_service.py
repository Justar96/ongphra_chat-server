from typing import Optional
import aiohttp
import json
import os
from fastapi import Depends

from app.core.logging import get_logger
from app.config.settings import Settings, get_settings

class OpenAIService:
    """Service for interacting with OpenAI API to generate fortune readings"""
    
    def __init__(self):
        """Initialize the OpenAI service"""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.settings = get_settings()
        
        # Get API key from settings or environment
        self.api_key = self.settings.openai_api_key
        if not self.api_key:
            self.logger.warning("No OpenAI API key found, AI reading generation will be disabled")
            
        self.api_base = self.settings.openai_api_base
        self.model = self.settings.openai_model
        
        self.logger.info(f"Initialized OpenAIService with model: {self.model}")
    
    async def chat_completion(
        self, 
        system_prompt: str, 
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate text using OpenAI's chat completion API
        
        Args:
            system_prompt: The system prompt to guide the AI's behavior
            user_prompt: The user's message/input
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0-1)
            
        Returns:
            Generated text or None if request fails
        """
        if not self.api_key:
            self.logger.error("Cannot generate AI reading: No API key configured")
            return None
            
        try:
            self.logger.info(f"Generating reading with {len(user_prompt)} chars of user prompt")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base}/chat/completions"
                async with session.post(url, headers=headers, data=json.dumps(data)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return None
                        
                    result = await response.json()
                    
                    if not result.get("choices") or len(result["choices"]) == 0:
                        self.logger.error(f"Invalid response from OpenAI: {result}")
                        return None
                        
                    generated_text = result["choices"][0]["message"]["content"].strip()
                    
                    # Log truncated output
                    preview = generated_text[:100] + "..." if len(generated_text) > 100 else generated_text
                    self.logger.info(f"Generated reading: {preview}")
                    
                    return generated_text
                    
        except Exception as e:
            self.logger.error(f"Error in chat completion: {str(e)}", exc_info=True)
            return None
    
    async def is_available(self) -> bool:
        """Check if the OpenAI service is configured and available"""
        return bool(self.api_key)


# Factory function for dependency injection
async def get_openai_service() -> OpenAIService:
    """Get OpenAI service instance"""
    return OpenAIService() 