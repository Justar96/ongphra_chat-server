import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.ai_topic_service import AITopicService
from app.services.reading_service import ReadingService
from app.repository.reading_repository import ReadingRepository
from app.repository.category_repository import CategoryRepository
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("test_ai_topic")

async def test_topic_detection():
    """Test AI topic detection"""
    logger.info("Testing AI topic detection...")
    
    # Create AI topic service
    ai_topic_service = AITopicService()
    
    # Test with various messages
    test_messages = [
        "ช่วยทำนายเรื่องความรักให้หน่อย ฉันกำลังจะแต่งงาน",
        "ฉันจะรวยไหม",
        "ที่ทำงานฉันจะได้เลื่อนตำแหน่งหรือเปล่า",
        "สุขภาพในอนาคตจะเป็นอย่างไร",
        "ฉันควรจะย้ายบ้านในปีนี้ไหม"
    ]
    
    for message in test_messages:
        result = await ai_topic_service.detect_topic(message)
        logger.info(f"\nMessage: {message}")
        logger.info(f"Detected topic: {result['primary_topic']} with confidence {result['confidence']}")
        logger.info(f"Reasoning: {result['reasoning']}")
        logger.info(f"Secondary topics: {result['secondary_topics']}")
        logger.info("---")
    
    logger.info("AI topic detection test completed")

async def test_fortune_reading_with_topic():
    """Test fortune reading with topic detection"""
    logger.info("Testing fortune reading with topic detection...")
    
    # Initialize services
    reading_repository = ReadingRepository()
    category_repository = CategoryRepository()
    reading_service = ReadingService(reading_repository, category_repository)
    
    # Test cases with birth date
    birth_date = datetime(1996, 2, 14)
    thai_day = "พุธ"
    test_cases = [
        {
            "question": "ฉันจะมีโชคลาภทางการเงินไหม",
            "expected_topic": "การเงิน"
        },
        {
            "question": "ความรักของฉันจะเป็นอย่างไร",
            "expected_topic": "ความรัก"
        },
        {
            "question": "สุขภาพในปีนี้จะดีไหม",
            "expected_topic": "สุขภาพ"
        }
    ]
    
    for case in test_cases:
        logger.info(f"\nTesting question: {case['question']}")
        logger.info(f"Expected topic: {case['expected_topic']}")
        
        try:
            reading = await reading_service.get_fortune_reading(
                birth_date=birth_date,
                thai_day=thai_day,
                user_question=case['question']
            )
            
            logger.info(f"Got reading with heading: {reading.heading}")
            logger.info(f"Meaning: {reading.meaning}")
            logger.info(f"Influence type: {reading.influence_type}")
            logger.info("---")
            
        except Exception as e:
            logger.error(f"Test failed with error: {str(e)}")
            raise
    
    logger.info("Fortune reading test completed")

async def test_topic_caching():
    """Test topic detection caching"""
    logger.info("Testing topic detection caching...")
    
    # Create AI topic service
    ai_topic_service = AITopicService()
    
    # Test message
    test_message = "ฉันจะมีโชคลาภทางการเงินไหม"
    
    # First detection
    logger.info("First detection...")
    result1 = await ai_topic_service.detect_topic(test_message)
    
    # Second detection (should use cache)
    logger.info("Second detection (should use cache)...")
    result2 = await ai_topic_service.detect_topic(test_message)
    
    # Verify results are the same
    assert result1 == result2, "Cached result does not match original"
    
    logger.info("Topic caching test completed")

async def main():
    """Run all tests"""
    logger.info("Starting AI topic service tests...")
    
    try:
        # Test AI topic detection
        await test_topic_detection()
        
        # Test fortune reading with topic detection
        await test_fortune_reading_with_topic()
        
        # Test topic caching
        await test_topic_caching()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        raise
    
    logger.info("AI topic service tests completed.")

if __name__ == "__main__":
    asyncio.run(main()) 