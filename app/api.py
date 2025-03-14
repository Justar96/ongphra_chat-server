from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from .calculator import ThaiBirthCalculator
from .meaning_engine import MeaningEngine
from .prompt_engine import PromptEngine
from .settings import CATEGORIES_PATH, READINGS_PATH

# Create the FastAPI application instance
api_app = FastAPI()  # Changed the variable name to api_app to avoid confusion

calculator = ThaiBirthCalculator()
meaning_engine = MeaningEngine()
prompt_engine = PromptEngine()

class FortuneRequest(BaseModel):
    birth_date: str  # Format: YYYY-MM-DD
    thai_day: str  # Thai day name
    question: str
    language: Optional[str] = "thai"  # Default to Thai

@api_app.post("/fortune")
async def get_fortune(request: FortuneRequest):
    try:
        # Parse the birth date
        birth_date = datetime.strptime(request.birth_date, "%Y-%m-%d")
        
        # Calculate the bases
        results = calculator.calculate_birth_bases(birth_date, request.thai_day)
        
        # Extract meanings based on the question
        meanings = meaning_engine.extract_meanings(results["bases"], request.question)
        
        # Generate response
        response = await prompt_engine.generate_response(
            results["birth_info"],
            results["bases"],
            meanings,
            request.question,
            request.language
        )
        
        return {
            "fortune": response,
            "bases": results["bases"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")