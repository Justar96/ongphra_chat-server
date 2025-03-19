# app/tests/test_fortune_flow.py
import asyncio
import sys
import os
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.utils.ai_tools import process_fortune_tool
from app.utils.fortune_tool import handle_fortune_request
from app.services.reading_service import get_reading_service
from app.services.calculator import CalculatorService
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("test_fortune_flow")

async def test_fortune_detection():
    """Test whether fortune detection is working correctly"""
    logger.info("Testing fortune detection...")
    
    # Test fortune detection with a fortune-related message
    fortune_message = "ช่วยทำนายชะตาชีวิตให้หน่อย"
    user_id = "test_user_1"
    
    # Call the process_fortune_tool function
    result = await process_fortune_tool(fortune_message, user_id)
    
    # Output the result
    logger.info(f"Fortune detection result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Check if the message was detected as a fortune request
    assert result["is_fortune_request"] == True, "Failed to detect fortune request"
    logger.info("Fortune detection test passed ✓")
    
    return result

async def test_fortune_with_birthdate():
    """Test fortune processing with birth date"""
    logger.info("Testing fortune with birth date...")
    
    # Test with a fortune request that includes a birth date
    message_with_birthdate = "ช่วยทำนายชะตาชีวิตให้หน่อย ฉันเกิดวันที่ 14/02/1996"
    user_id = "test_user_2"
    
    # Call the process_fortune_tool function
    result = await process_fortune_tool(message_with_birthdate, user_id)
    
    # Output the result
    logger.info(f"Fortune with birthdate result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Check if the birth date was extracted correctly
    assert result["extracted_birthdate"] is not None, "Failed to extract birth date"
    logger.info("Birth date extraction test passed ✓")
    
    # Check if a fortune reading was generated
    assert result["fortune_reading"] is not None, "Failed to generate fortune reading"
    logger.info("Fortune reading generation test passed ✓")
    
    return result

async def test_calculator_service():
    """Test the calculator service directly"""
    logger.info("Testing calculator service...")
    
    # Create a calculator service instance
    calculator = CalculatorService()
    
    # Test with a sample birth date
    birth_date = datetime(1996, 2, 14)
    thai_day = "พุธ"  # Wednesday
    
    # Calculate birth bases
    bases_result = calculator.calculate_birth_bases(birth_date, thai_day)
    
    # Output the result
    logger.info(f"Calculator result: {bases_result}")
    
    # Check if bases were calculated correctly
    assert bases_result is not None, "Failed to calculate birth bases"
    logger.info("Calculator service test passed ✓")
    
    return bases_result

async def test_reading_service():
    """Test the reading service directly"""
    logger.info("Testing reading service...")
    
    # Get the reading service
    reading_service = await get_reading_service()
    
    # Test with a sample birth date
    birth_date = datetime(1996, 2, 14)
    thai_day = "พุธ"  # Wednesday
    
    # Get a fortune reading
    reading = await reading_service.get_fortune_reading(
        birth_date=birth_date,
        thai_day=thai_day,
        question="ช่วยทำนายชะตาชีวิตให้หน่อย",
        user_id="test_user_3"
    )
    
    # Output the result
    logger.info(f"Reading service result: {reading}")
    
    # Check if a reading was generated
    assert reading is not None, "Failed to generate reading"
    logger.info("Reading service test passed ✓")
    
    return reading

async def main():
    """Run all tests"""
    logger.info("Starting fortune system tests...")
    
    try:
        # Test 1: Fortune detection
        fortune_detection_result = await test_fortune_detection()
        
        # Test 2: Fortune with birth date
        fortune_with_birthdate_result = await test_fortune_with_birthdate()
        
        # Test 3: Calculator service
        calculator_result = await test_calculator_service()
        
        # Test 4: Reading service
        reading_result = await test_reading_service()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        
    logger.info("Fortune system tests completed.")

if __name__ == "__main__":
    asyncio.run(main()) 