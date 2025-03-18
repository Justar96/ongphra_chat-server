import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from ongphra_chat.app.services.meaning import MeaningService
from ongphra_chat.app.services.calculator import CalculatorService
from ongphra_chat.app.domain.birth import BirthInfo
from ongphra_chat.app.domain.bases import Bases
from ongphra_chat.app.repository.category_repository import CategoryRepository
from ongphra_chat.app.repository.reading_repository import ReadingRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("test_meaning_service")

async def test_meaning_service():
    """Test the MeaningService functionality"""
    logger.info("Starting MeaningService test")
    
    # Initialize repositories
    category_repo = CategoryRepository()
    reading_repo = ReadingRepository()
    
    # Initialize services
    calculator_service = CalculatorService()
    meaning_service = MeaningService(category_repo, reading_repo)
    
    # Create a test birth info
    birth_date = datetime(1990, 1, 1)
    thai_day = "จันทร์"  # Monday
    birth_info = BirthInfo(
        birth_date=birth_date,
        thai_day=thai_day
    )
    
    # Calculate bases
    bases = calculator_service.calculate_bases(birth_info)
    logger.info(f"Calculated bases: {bases}")
    
    # Test topic identification
    test_questions = [
        "ฉันจะมีความรักที่ดีเมื่อไหร่",
        "การเงินของฉันในปีนี้จะเป็นอย่างไร",
        "อาชีพของฉันจะก้าวหน้าหรือไม่",
        "สุขภาพของฉันในอนาคตจะเป็นอย่างไร",
        "ครอบครัวของฉันจะมีความสุขหรือไม่"
    ]
    
    for question in test_questions:
        topics = meaning_service._identify_topics(question)
        logger.info(f"Question: '{question}' -> Topics: {topics}")
    
    # Test meaning extraction
    for question in test_questions:
        try:
            meanings = await meaning_service.extract_meanings(bases, question)
            logger.info(f"Question: '{question}' -> Found {len(meanings.items)} meanings")
            
            # Print the first few meanings
            for i, meaning in enumerate(meanings.items[:3]):
                logger.info(f"  Meaning {i+1}: {meaning.heading} - {meaning.category}")
                logger.info(f"    Base: {meaning.base}, Position: {meaning.position}, Value: {meaning.value}")
                logger.info(f"    Content: {meaning.meaning[:50]}...")
        except Exception as e:
            logger.error(f"Error extracting meanings for question '{question}': {str(e)}", exc_info=True)
    
    logger.info("MeaningService test completed")

if __name__ == "__main__":
    asyncio.run(test_meaning_service()) 