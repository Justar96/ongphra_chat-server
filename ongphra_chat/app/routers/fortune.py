import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
import json
import uuid

from app.models.schemas import (
    ChatRequest, FortuneRequest, FortuneResponse, FortuneResult,
    IndividualInterpretation, CombinationInterpretation,
    ResponseStatus, ChatResponse, ApiResponse,
    FortuneExplanation, FortuneExplanationResponse,
    ChatCompletion, ChatChoice
)
from app.utils.openai_client import OpenAIClient, get_openai_client
from app.utils.fortune_calculator import calculate_fortune
from app.utils.fortune_interpreter import FortuneInterpreter, get_fortune_interpreter
from app.services.chat_service import ChatService, get_chat_service

router = APIRouter(tags=["fortune"])
logger = logging.getLogger(__name__)

@router.post("/fortune", response_model=FortuneResponse, summary="Calculate fortune based on birthdate")
async def calculate_fortune_endpoint(
    request: FortuneRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Calculate a fortune based on birthdate using Thai 7-base-9 numerology.
    
    The calculation is based on traditional Thai fortune telling techniques and includes:
    - Base 1: Day of birth values
    - Base 2: Month of birth values
    - Base 3: Year of birth values
    - Base 4: Combined values
    
    The result includes raw values and various interpretations of their meaning.
    """
    try:
        # Calculate the fortune
        fortune_data = calculate_fortune(request.birthdate)
        
        # Store the fortune calculation if session is provided
        if request.session_id and request.user_id:
            # Store calculation in database
            await chat_service.store_fortune_calculation_async(
                session_id=request.session_id,
                user_id=request.user_id,
                birthdate=request.birthdate,
                fortune_result=fortune_data
            )
        
        # Convert to FortuneResult model
        result = FortuneResult(
            bases=fortune_data,
            user_id=request.user_id or str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            timestamp=int(__import__('time').time())
        )
        
        # Build the response
        response = FortuneResponse(
            status=ResponseStatus(success=True),
            result=result
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error calculating fortune: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error calculating fortune: {str(e)}")

@router.post("/fortune/narrative", response_model=ApiResponse, summary="Generate narrative fortune interpretation")
async def generate_fortune_narrative(
    request: FortuneRequest,
    fortune_interpreter: FortuneInterpreter = Depends(get_fortune_interpreter),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Generate a narrative interpretation of the fortune calculation using AI.
    This provides a more natural, conversational response based on the raw data.
    """
    try:
        # First calculate the fortune
        fortune_data = calculate_fortune(request.birthdate)
        
        # Generate the narrative interpretation
        language = request.language if hasattr(request, 'language') else "thai"
        narrative = await fortune_interpreter.generate_interpretation(
            fortune_data=fortune_data,
            language=language,
            birthdate=request.birthdate
        )
        
        # Store the fortune calculation if session is provided
        if request.session_id and request.user_id:
            # Store calculation in database
            await chat_service.store_fortune_calculation_async(
                session_id=request.session_id,
                user_id=request.user_id,
                birthdate=request.birthdate,
                fortune_result=fortune_data
            )
            
            # Also store the narrative as an assistant message
            await chat_service.add_message_async(
                session_id=request.session_id,
                user_id=request.user_id,
                role="assistant",
                content=narrative,
                is_fortune=True
            )
        
        # Create the response
        user_id = request.user_id or str(uuid.uuid4())
        response = ApiResponse(
            status=ResponseStatus(success=True),
            user_id=user_id,
            request_id=str(uuid.uuid4()),
            data={
                "narrative": narrative,
                "raw_fortune": fortune_data
            }
        )
        
        return response
    except Exception as e:
        logger.error(f"Error generating fortune narrative: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating fortune narrative: {str(e)}")

@router.get("/fortune/explanation", response_model=FortuneExplanationResponse, summary="Get explanation of fortune system")
async def get_fortune_explanation(
    openai_client: OpenAIClient = Depends(get_openai_client)
):
    """
    Get an explanation of the Thai fortune (7N9B) system using AI.
    This endpoint returns an AI-generated explanation of how the system works.
    """
    try:
        # Use OpenAI to generate an explanation
        explanation_prompt = """
        Explain the Thai 7-base-9 (7N9B) fortune telling system in a clear, concise way.
        Include what the system is, how it works, and the meaning of the bases.
        Structure your response as a JSON object with the following fields:
        - system_name: The name of the system
        - description: A brief description of the system
        - bases: An object describing the four bases
        - interpretation: How to interpret the numbers
        
        Keep your response concise and factual.
        """
        
        completion = await openai_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are an expert in Thai fortune telling systems. Respond with JSON only."},
                {"role": "user", "content": explanation_prompt}
            ]
        )
        
        # Extract the content from the completion
        content = completion["choices"][0]["message"]["content"]
        
        # Try to parse the JSON
        try:
            explanation_data = json.loads(content)
        except json.JSONDecodeError:
            # If the AI didn't return valid JSON, create a default explanation
            explanation_data = {
                "system_name": "เลข 7 ฐาน 9 (7N9B)",
                "description": "เลข 7 ฐาน 9 คือศาสตร์การทำนายโชคชะตาโบราณของไทย โดยใช้วันเกิดคำนวณตัวเลขและความหมายต่างๆ",
                "bases": {
                    "base1": "เกี่ยวกับวันเกิด - อัตตะ, หินะ, ธานัง, ปิตา, มาตา, โภคา, มัชฌิมา",
                    "base2": "เกี่ยวกับเดือนเกิด - ตะนุ, กดุมภะ, สหัชชะ, พันธุ, ปุตตะ, อริ, ปัตนิ",
                    "base3": "เกี่ยวกับปีเกิด - มรณะ, สุภะ, กัมมะ, ลาภะ, พยายะ, ทาสา, ทาสี",
                    "base4": "ผลรวมของฐาน 1-3"
                },
                "interpretation": "ตัวเลขที่สูงในแต่ละฐานแสดงถึงอิทธิพลที่มีผลต่อชีวิตในด้านนั้นๆ"
            }
        
        # Create the response
        explanation = FortuneExplanation(**explanation_data)
        
        response = FortuneExplanationResponse(
            status=ResponseStatus(success=True),
            data=explanation,
            timestamp=int(__import__('time').time())
        )
        
        return response
    except Exception as e:
        logger.error(f"Error generating fortune system explanation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating fortune system explanation: {str(e)}")