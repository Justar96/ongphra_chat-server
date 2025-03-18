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
from ongphra_chat.app.repository.mock_repository import MockCategoryRepository, MockReadingRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("test_meaning_service_mock")

async def test_meaning_service():
    """Test the MeaningService functionality with mock repositories"""
    logger.info("Starting MeaningService test with mock repositories")
    
    # Initialize mock repositories
    category_repo = MockCategoryRepository()
    reading_repo = MockReadingRepository()
    
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
    
    # Create test bases
    base1 = [1, 2, 3, 4, 5, 6, 7]
    base2 = [2, 3, 4, 5, 6, 7, 1]
    base3 = [3, 4, 5, 6, 7, 1, 2]
    base4 = [4, 5, 6, 7, 1, 2, 3]
    
    bases = Bases(
        base1=base1,
        base2=base2,
        base3=base3,
        base4=base4
    )
    
    logger.info(f"Created test bases: {bases}")
    
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
    
    # Test get_meaning_by_base_position
    for base in range(1, 5):
        for position in range(1, 8):
            try:
                meaning = await meaning_service.get_meaning_by_base_position(base, position, bases)
                if meaning:
                    logger.info(f"Base {base}, Position {position} -> Found meaning: {meaning.heading}")
                else:
                    logger.info(f"Base {base}, Position {position} -> No meaning found")
            except Exception as e:
                logger.error(f"Error getting meaning for base {base}, position {position}: {str(e)}", exc_info=True)
    
    logger.info("MeaningService test with mock repositories completed")

if __name__ == "__main__":
    asyncio.run(test_meaning_service()) 