# app/core/service.py
from datetime import datetime
from typing import Dict, List, Optional, Any

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
    
    async def get_fortune(
        self,
        birth_date: datetime,
        thai_day: str,
        question: str,
        language: str = "thai"
    ) -> FortuneResponse:
        """
        Main method to generate a fortune reading based on birth information and question.
        
        Args:
            birth_date: User's birth date
            thai_day: Thai day name
            question: User's question
            language: Response language (thai or english)
            
        Returns:
            FortuneResponse object with fortune text and calculation results
        """
        try:
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
            try:
                fortune_text = await self.response_service.generate_response(
                    prompt, 
                    language,
                    has_birth_info=True
                )
            except Exception as e:
                # If response generation fails, provide a fallback
                if language.lower() == "english":
                    fortune_text = "I apologize, but I'm unable to provide a detailed reading at this moment. Please try again later."
                else:
                    fortune_text = "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"
                print(f"Error in response generation: {str(e)}")
            
            # Step 5: Create and return response object
            return FortuneResponse(
                fortune=fortune_text,
                birth_info=calculation_result.birth_info,
                bases=calculation_result.bases,
                meanings=meanings
            )
            
        except Exception as e:
            # Handle any errors
            print(f"Error in get_fortune: {str(e)}")
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
        language: str = "thai"
    ) -> str:
        """
        Generate a general response without birth information.
        
        Args:
            question: User's question
            language: Response language (thai or english)
            
        Returns:
            General fortune response text
        """
        try:
            # Generate a prompt without birth info
            prompt = self.prompt_service.generate_user_prompt(
                birth_info=None,
                bases=None,
                meanings=None,
                question=question,
                language=language
            )
            
            # Generate response using AI
            response_text = await self.response_service.generate_response(
                prompt,
                language,
                has_birth_info=False
            )
            
            return response_text
            
        except Exception as e:
            # Handle any errors with a fallback response
            print(f"Error generating general response: {str(e)}")
            if language.lower() == "english":
                return "I apologize, but I'm unable to provide a reading at this moment. Please try again later."
            else:
                return "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"