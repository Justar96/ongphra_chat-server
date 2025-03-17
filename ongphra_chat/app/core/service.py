# app/core/service.py
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
import time
import asyncio
import logging
import sys

from app.domain.birth import BirthInfo
from app.domain.bases import BasesResult, Bases
from app.domain.meaning import MeaningCollection, Meaning
from app.domain.response import FortuneResponse
from app.services.calculator import CalculatorService
from app.services.meaning import MeaningService
from app.services.prompt import PromptService
from app.services.response import ResponseService
from app.core.exceptions import FortuneServiceException
from app.core.logging import get_logger


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
        
        # Add error handling for logger initialization
        try:
            self.logger = get_logger(__name__)
            self.logger.info("Initialized FortuneService")
        except Exception as e:
            # Fallback to basic console logging if file logging fails
            self.logger = logging.getLogger(__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
            self.logger.warning(f"Failed to initialize file logger: {str(e)}. Using console logger instead.")
            self.logger.info("Initialized FortuneService with fallback console logger")
        
        # Track user sessions with expiration time
        self.user_sessions = {}
        
        # Session cleanup settings
        self.cleanup_interval = 3600  # 1 hour
        self.session_max_age = 24 * 3600  # 24 hours
        
        # Start background cleanup task
        self._start_cleanup_task()
    
    def _update_user_session(self, user_id: str, birth_date: Optional[datetime], thai_day: Optional[str], language: str):
        """Update user session information"""
        self.logger.debug(f"Updating session for user {user_id}")
        self.user_sessions[user_id] = {
            "birth_date": birth_date,
            "thai_day": thai_day,
            "language": language,
            "last_interaction": datetime.now(),
            "expiration": datetime.now() + timedelta(seconds=self.session_max_age)
        }
    
    async def _start_cleanup_task(self):
        """Start a background task to clean up old sessions"""
        try:
            # Use asyncio.create_task in real implementation
            # For simplicity, we're just defining the method here
            pass
        except Exception as e:
            self.logger.error(f"Failed to start cleanup task: {str(e)}")
    
    async def _cleanup_old_sessions(self):
        """Background task to remove expired sessions"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self.cleanup_old_sessions()
            except Exception as e:
                self.logger.error(f"Error in session cleanup: {str(e)}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
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
        start_time = time.time()
        self.logger.info(f"Getting fortune for user {user_id}: birth_date={birth_date}, thai_day={thai_day}, language={language}")
        
        try:
            # Validate inputs
            if not birth_date:
                raise FortuneServiceException("Birth date is required")
            if not thai_day:
                raise FortuneServiceException("Thai day is required")
                
            # Update or initialize user session
            self._update_user_session(user_id, birth_date, thai_day, language)
            
            # Step 1: Calculate bases from birth info
            calculation_result = self.calculator_service.calculate_birth_bases(
                birth_date, thai_day
            )
            
            calculation_time = time.time()
            self.logger.debug(f"Calculation completed in {calculation_time - start_time:.2f}s")
            
            # Step 2: Extract meanings from bases
            meanings = await self.meaning_service.extract_meanings(
                calculation_result.bases, question
            )
            
            meanings_time = time.time()
            self.logger.debug(f"Meaning extraction completed in {meanings_time - calculation_time:.2f}s")
            
            # Step 3: Generate prompt for OpenAI
            prompt = self.prompt_service.generate_user_prompt(
                calculation_result.birth_info,
                calculation_result.bases,
                meanings,
                question,
                language
            )
            
            prompt_time = time.time()
            self.logger.debug(f"Prompt generation completed in {prompt_time - meanings_time:.2f}s")
            
            # Step 4: Generate response using AI
            if stream:
                # For streaming responses, return the generator directly
                self.logger.info(f"Returning streaming response for user {user_id}")
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
                    
                    response_time = time.time()
                    self.logger.debug(f"Response generation completed in {response_time - prompt_time:.2f}s")
                    self.logger.info(f"Total fortune generation completed in {response_time - start_time:.2f}s")
                    
                except Exception as e:
                    # If response generation fails, provide a fallback
                    self.logger.error(f"Error in response generation: {str(e)}", exc_info=True)
                    if language.lower() == "english":
                        fortune_text = "I apologize, but I'm unable to provide a detailed reading at this moment. Please try again later."
                    else:
                        fortune_text = "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
                
                # Return FortuneResponse object
                return FortuneResponse(
                    fortune=fortune_text,
                    birth_info=calculation_result.birth_info,
                    bases=calculation_result.bases,
                    meanings=meanings
                )
            
        except FortuneServiceException as e:
            # Handle known service exceptions
            self.logger.error(f"Fortune service exception: {str(e)}")
            raise
        except Exception as e:
            # Handle any errors
            self.logger.error(f"Error in get_fortune: {str(e)}", exc_info=True)
            
            if stream:
                # Create an async generator for the error message
                async def error_generator():
                    error_msg = "An error occurred during fortune generation. Please try again later."
                    if language.lower() != "english":
                        error_msg = "เกิดข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
                    yield error_msg
                
                return error_generator()
            else:
                # Return error response
                error_msg = "An error occurred during fortune generation. Please try again later."
                if language.lower() != "english":
                    error_msg = "เกิดข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
                
                return FortuneResponse(
                    fortune=error_msg,
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
        Generate a general response when no birth information is provided
        
        Args:
            question: User's question
            language: Response language (thai or english)
            user_id: User identifier for conversation tracking
            stream: Whether to return a streaming response
            
        Returns:
            General fortune telling response or streaming generator
        """
        start_time = time.time()
        self.logger.info(f"Getting general response for user {user_id}: question='{question}', language={language}")
        
        try:
            # Generate prompt for general response
            prompt = f"Question: {question}"
            
            # Generate response using AI
            if stream:
                # For streaming responses, return the generator directly
                self.logger.info(f"Returning streaming general response for user {user_id}")
                generator = self.response_service.generate_response(
                    prompt, 
                    language,
                    has_birth_info=False,
                    user_id=user_id,
                    stream=True
                )
                # Return the generator directly, not as a coroutine
                return generator
            else:
                # For standard responses, return the text directly
                try:
                    fortune_text = await self.response_service.generate_response(
                        prompt, 
                        language,
                        has_birth_info=False,
                        user_id=user_id,
                        stream=False
                    )
                    
                    response_time = time.time()
                    self.logger.info(f"General response generated in {response_time - start_time:.2f}s")
                    
                    return fortune_text
                    
                except Exception as e:
                    # If response generation fails, provide a fallback
                    self.logger.error(f"Error in general response generation: {str(e)}", exc_info=True)
                    if language.lower() == "english":
                        return "I apologize, but I'm unable to provide a response at this moment. Please try again later."
                    else:
                        return "ขออภัย มีข้อผิดพลาดในการตอบคำถาม กรุณาลองใหม่อีกครั้ง"
            
        except Exception as e:
            # Handle any errors
            self.logger.error(f"Error in get_general_response: {str(e)}", exc_info=True)
            
            if stream:
                # Create an async generator for the error message
                async def error_generator():
                    error_msg = "An error occurred. Please try again later."
                    if language.lower() != "english":
                        error_msg = "เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
                    yield error_msg
                
                return error_generator()
            else:
                # Return error message
                error_msg = "An error occurred. Please try again later."
                if language.lower() != "english":
                    error_msg = "เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
                
                return error_msg