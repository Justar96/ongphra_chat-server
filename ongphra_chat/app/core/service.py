# app/core/service.py
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator, Union

from app.domain.birth import BirthInfo
from app.domain.bases import BasesResult
from app.domain.meaning import MeaningCollection
from app.domain.response import FortuneResponse
from app.services.calculator import CalculatorService
from app.services.meaning import MeaningService
from app.services.prompt import PromptService
from app.services.response import ResponseService
from app.core.exceptions import FortuneServiceException


class FortuneService:
    """
    Core service that orchestrates the fortune telling process.
    This is the main entry point for the application logic.
    """
    
    def __init__(
        self,
        calculator_service: CalculatorService,
        meaning_service: MeaningService,
        prompt_service: PromptService,
        response_service: ResponseService
    ):
        self.calculator_service = calculator_service
        self.meaning_service = meaning_service
        self.prompt_service = prompt_service
        self.response_service = response_service
        
        # Track user sessions
        self.user_sessions = {}
    
    def _update_user_session(self, user_id: str, birth_date: datetime, thai_day: str, language: str):
        """Update user session information"""
        self.user_sessions[user_id] = {
            "birth_date": birth_date,
            "thai_day": thai_day,
            "language": language,
            "last_interaction": datetime.now()
        }
    
    async def get_fortune(
        self,
        birth_date: datetime,
        thai_day: str,
        question: str,
        language: str = "thai",
        user_id: str = "default_user",
        stream: bool = False
    ) -> Union[FortuneResponse, AsyncGenerator[str, None]]:
        """
        Main method to generate a fortune reading based on birth information and question.
        
        Args:
            birth_date: User's birth date
            thai_day: Thai day name
            question: User's question
            language: Response language (thai or english)
            user_id: User identifier for conversation tracking
            stream: Whether to return a streaming response
            
        Returns:
            FortuneResponse object or streaming generator depending on stream parameter
        """
        try:
            # Update or initialize user session
            self._update_user_session(user_id, birth_date, thai_day, language)
            
            # Step 1: Calculate bases from birth info
            calculation_result = self.calculator_service.calculate_birth_bases(
                birth_date, thai_day
            )
            
            # Step 2: Extract meanings from bases
            meanings = await self.meaning_service.extract_meanings(
                calculation_result.bases, question
            )
            
            # Step 3: Generate prompt for OpenAI
            prompt = self.prompt_service.generate_user_prompt(
                calculation_result.birth_info,
                calculation_result.bases,
                meanings,
                question,
                language
            )
            
            # Step 4: Generate response using AI
            if stream:
                # For streaming responses, return the generator directly
                return await self.response_service.generate_response(
                    prompt, 
                    language,
                    has_birth_info=True,
                    user_id=user_id,
                    stream=True
                )
            else:
                # For standard responses, create a FortuneResponse object
                try:
                    fortune_text = await self.response_service.generate_response(
                        prompt, 
                        language,
                        has_birth_info=True,
                        user_id=user_id,
                        stream=False
                    )
                except Exception as e:
                    # If response generation fails, provide a fallback
                    if language.lower() == "english":
                        fortune_text = "I apologize, but I'm unable to provide a detailed reading at this moment. Please try again later."
                    else:
                        fortune_text = "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
                    print(f"Error in response generation: {str(e)}")
                
                # Return FortuneResponse object
                return FortuneResponse(
                    fortune=fortune_text,
                    birth_info=calculation_result.birth_info,
                    bases=calculation_result.bases,
                    meanings=meanings
                )
            
        except Exception as e:
            # Handle any errors
            print(f"Error in get_fortune: {str(e)}")
            
            if stream:
                # Create an async generator for the error message
                async def error_generator():
                    if language.lower() == "english":
                        yield "I apologize, but I'm unable to provide a reading at this moment. Please try again later."
                    else:
                        yield "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
                
                return error_generator()
            else:
                # Create a minimal response with just the fortune text
                if language.lower() == "english":
                    fallback = "I apologize, but I'm unable to provide a reading at this moment. Please try again later."
                else:
                    fallback = "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
                    
                return FortuneResponse(
                    fortune=fallback,
                    birth_info=None,
                    bases=None,
                    meanings=None
                )
    
    async def get_general_response(
        self,
        question: str,
        language: str = "thai",
        user_id: str = "default_user",
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate a general response without birth information.
        
        Args:
            question: User's question
            language: Response language (thai or english)
            user_id: User identifier for conversation tracking
            stream: Whether to return a streaming response
            
        Returns:
            General fortune response text or streaming generator
        """
        try:
            # Update user session language
            if user_id in self.user_sessions:
                self.user_sessions[user_id]["language"] = language
                self.user_sessions[user_id]["last_interaction"] = datetime.now()
            else:
                self.user_sessions[user_id] = {
                    "language": language,
                    "birth_date": None,
                    "thai_day": None,
                    "last_interaction": datetime.now()
                }
            
            # Generate a prompt without birth info
            prompt = self.prompt_service.generate_user_prompt(
                birth_info=None,
                bases=None,
                meanings=None,
                question=question,
                language=language
            )
            
            # Generate response using AI (streaming or standard)
            return await self.response_service.generate_response(
                prompt,
                language,
                has_birth_info=False,
                user_id=user_id,
                stream=stream
            )
            
        except Exception as e:
            # Handle any errors with a fallback response
            print(f"Error generating general response: {str(e)}")
            
            if stream:
                # Create an async generator for the error message
                async def error_generator():
                    if language.lower() == "english":
                        yield "I apologize, but I'm unable to provide a reading at this moment. Please try again later."
                    else:
                        yield "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
                
                return error_generator()
            else:
                if language.lower() == "english":
                    return "I apologize, but I'm unable to provide a reading at this moment. Please try again later."
                else:
                    return "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
                
    async def get_user_session_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a user's session"""
        return self.user_sessions.get(user_id)
        
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than the specified hours"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for user_id, session in self.user_sessions.items():
            last_interaction = session.get("last_interaction")
            if last_interaction:
                age = (current_time - last_interaction).total_seconds() / 3600
                if age > max_age_hours:
                    sessions_to_remove.append(user_id)
        
        for user_id in sessions_to_remove:
            del self.user_sessions[user_id]
            
        return len(sessions_to_remove)