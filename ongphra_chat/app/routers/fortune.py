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
from app.utils.openai_client import OpenAIClient
from app.utils.fortune_tool import calculate_7n9b_fortune

router = APIRouter(tags=["fortune"])
logger = logging.getLogger(__name__)

# Dependency to get OpenAI client
async def get_openai_client():
    client = OpenAIClient()
    try:
        yield client
    finally:
        await client.close()

@router.post("/chat", response_model=ChatResponse, summary="Chat with AI assistant")
async def chat(
    request: ChatRequest,
    openai_client: OpenAIClient = Depends(get_openai_client)
):
    """Chat with the AI assistant with optional streaming for Thai conversation and fortune telling."""
    try:
        # Convert Pydantic Message objects to dict for OpenAI API
        messages = [msg.to_dict() for msg in request.messages]
        
        # Generate user_id and session_id if not provided
        user_id = request.user_id or str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())
            
        if request.stream:
            return openai_client.create_streaming_response(messages)
        else:
            # Get OpenAI response
            openai_response = await openai_client.chat_completion(messages)
            
            # Convert to ChatCompletion model
            chat_completion = ChatCompletion(
                id=openai_response["id"],
                created=openai_response["created"],
                model=openai_response["model"],
                choices=[
                    ChatChoice(
                        index=i,
                        message=choice["message"],
                        finish_reason=choice["finish_reason"]
                    )
                    for i, choice in enumerate(openai_response["choices"])
                ],
                usage=openai_response.get("usage", None)
            )
            
            # Create response
            return ChatResponse(
                status=ResponseStatus(success=True),
                message_id=str(uuid.uuid4()),
                response=chat_completion,
                user_id=user_id,
                session_id=session_id
            )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@router.post("/fortune", response_model=FortuneResponse, summary="Calculate Thai Fortune")
async def calculate_fortune(
    request: FortuneRequest,
    openai_client: OpenAIClient = Depends(get_openai_client)
):
    """Calculate Thai fortune (7N9B) based on birthdate."""
    try:
        # Use the fortune calculation tool directly
        fortune_data = calculate_7n9b_fortune(request.birthdate)
        
        # Extract data from the result
        bases = fortune_data["bases"]
        individual_interpretations = [
            IndividualInterpretation(
                category=item["category"],
                meaning=item["meaning"],
                influence=item["influence"],
                value=item["value"],
                heading=item["heading"],
                detail=item["detail"]
            ) for item in fortune_data["individual_interpretations"]
        ]
        
        combination_interpretations = [
            CombinationInterpretation(
                category=item["category"],
                heading=item["heading"],
                meaning=item["meaning"],
                influence=item["influence"]
            ) for item in fortune_data["combination_interpretations"]
        ]
        
        # Create the result object
        result = FortuneResult(
            bases=bases,
            individual_interpretations=individual_interpretations,
            combination_interpretations=combination_interpretations,
            summary=fortune_data["summary"]
        )
        
        # Create the response
        user_id = request.user_id or str(uuid.uuid4())
        response = FortuneResponse(
            status=ResponseStatus(success=True),
            user_id=user_id,
            request_id=str(uuid.uuid4()),
            result=result
        )
        
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=400, 
            detail={"status": {"success": False, "message": str(e), "error_code": 400}}
        )
    except Exception as e:
        logger.error(f"Error calculating fortune: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={"status": {"success": False, "message": f"Error calculating fortune: {str(e)}", "error_code": 500}}
        )

@router.get("/fortune/explanation", response_model=FortuneExplanationResponse, summary="Get Fortune System Explanation")
async def get_fortune_explanation():
    """Get an explanation of the Thai fortune (7N9B) system."""
    explanation = FortuneExplanation(
        system_name="เลข 7 ฐาน 9 (7N9B)",
        description="เลข 7 ฐาน 9 คือศาสตร์การทำนายโชคชะตาโบราณของไทย โดยใช้วันเกิดคำนวณตัวเลขและความหมายต่างๆ",
        bases={
            "base1": "เกี่ยวกับวันเกิด - อัตตะ, หินะ, ธานัง, ปิตา, มาตา, โภคา, มัชฌิมา",
            "base2": "เกี่ยวกับเดือนเกิด - ตะนุ, กดุมภะ, สหัชชะ, พันธุ, ปุตตะ, อริ, ปัตนิ",
            "base3": "เกี่ยวกับปีเกิด - มรณะ, สุภะ, กัมมะ, ลาภะ, พยายะ, ทาสา, ทาสี",
            "base4": "ผลรวมของฐาน 1-3"
        },
        interpretation="ตัวเลขที่สูงในแต่ละฐานแสดงถึงอิทธิพลที่มีผลต่อชีวิตในด้านนั้นๆ"
    )
    
    response = FortuneExplanationResponse(
        status=ResponseStatus(success=True),
        data=explanation
    )
    
    return response