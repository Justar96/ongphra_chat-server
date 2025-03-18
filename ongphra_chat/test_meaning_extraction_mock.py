#!/usr/bin/env python
# test_meaning_extraction_mock.py
"""
Test script specifically for meaning extraction functionality using mock repositories
"""
import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from pprint import pprint

# Configure logging with a basic setup that works on Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("test_meaning_extraction_mock")

# Add the parent directory to path to find the app modules
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)
logger.info(f"Added {parent_dir} to Python path")

# Override the OpenAI API key from environment variable
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "dummy-api-key")
os.environ["DEFAULT_MODEL"] = os.environ.get("DEFAULT_MODEL", "gpt-4o-mini")

try:
    # Import necessary modules
    logger.info("Importing modules...")
    from app.repository.mock_repository import MockCategoryRepository, MockReadingRepository
    from app.domain.bases import Bases, BasesResult, BirthInfo
    from app.domain.meaning import Meaning, MeaningCollection
    logger.info("Modules imported successfully")
except Exception as e:
    logger.error(f"Error importing modules: {str(e)}", exc_info=True)
    sys.exit(1)

# Create mock MeaningService using the MockCategoryRepository
class MockMeaningService:
    """Mock service for meaning extraction and topic identification"""
    
    def __init__(self):
        """Initialize the mock meaning service"""
        self.logger = logger
        self.category_repository = MockCategoryRepository()
        self.reading_repository = MockReadingRepository()
        self._topic_cache = {}
        self._meaning_cache = {}
        self.CATEGORY_MAPPINGS = {
            'RELATIONSHIP': {'thai_meaning': 'relationship', 'house_number': 5, 'house_type': 'personal'},
            'FINANCE': {'thai_meaning': 'finance', 'house_number': 2, 'house_type': 'material'},
            'CAREER': {'thai_meaning': 'career', 'house_number': 6, 'house_type': 'work'},
            'HEALTH': {'thai_meaning': 'health', 'house_number': 6, 'house_type': 'physical'},
            'FAMILY': {'thai_meaning': 'family', 'house_number': 4, 'house_type': 'personal'}
        }
    
    async def _identify_topics_with_ai(self, question: str) -> list:
        """Mock implementation of AI topic identification"""
        # Check cache first
        if question in self._topic_cache:
            return list(self._topic_cache[question])
        
        self.logger.info(f"Identifying topics for question ID: {id(question)}")
        
        # Simple keyword-based topic identification for testing
        topics = []
        
        if "รัก" in question or "แฟน" in question or "คู่" in question:
            topics.append("RELATIONSHIP:FINANCE")
        
        if "เงิน" in question or "ทรัพย์" in question or "การเงิน" in question:
            topics.append("FINANCE:CAREER")
        
        if "งาน" in question or "อาชีพ" in question or "การงาน" in question:
            topics.append("CAREER:HEALTH")
        
        if "สุขภาพ" in question or "ป่วย" in question or "โรค" in question:
            topics.append("HEALTH:FAMILY")
        
        if "ครอบครัว" in question or "พ่อ" in question or "แม่" in question:
            topics.append("FAMILY:RELATIONSHIP")
        
        if "อนาคต" in question:
            topics.append("CAREER:FINANCE")
        
        # Ensure we always have exactly 3 topic pairs
        if len(topics) == 0:
            # Default topics
            topics = ["RELATIONSHIP:FINANCE", "CAREER:HEALTH", "FAMILY:RELATIONSHIP"]
        elif len(topics) < 3:
            # Add default topics to reach 3
            default_topics = ["RELATIONSHIP:FINANCE", "CAREER:HEALTH", "FAMILY:RELATIONSHIP"]
            for topic in default_topics:
                if topic not in topics and len(topics) < 3:
                    topics.append(topic)
        elif len(topics) > 3:
            # Limit to 3 most relevant topics
            topics = topics[:3]
        
        # Cache the results
        self._topic_cache[question] = set(topics)
        
        return topics
    
    def _get_cache_key(self, bases: Bases, question: str) -> str:
        """Generate a cache key for the given bases and question"""
        base_str = f"{bases.base1}-{bases.base2}-{bases.base3}-{bases.base4}"
        return f"{base_str}:{question}"
    
    async def extract_meanings(self, bases: Bases, question: str) -> MeaningCollection:
        """Mock implementation of meaning extraction"""
        # Generate cache key
        cache_key = self._get_cache_key(bases, question)
        
        # Check cache first
        if cache_key in self._meaning_cache:
            self.logger.info(f"Using cached meanings for question ID: {id(question)}")
            return self._meaning_cache[cache_key]
        
        self.logger.info(f"Extracting meanings for question ID: {id(question)}")
        
        # Identify topics
        topics = await self._identify_topics_with_ai(question)
        self.logger.info(f"Identified topics: {topics}")
        
        # Create mock meanings based on topics
        meanings = []
        
        # Add one meaning for each topic
        for i, topic in enumerate(topics):
            if ":" in topic:
                parts = topic.split(":")
                primary = parts[0]
                secondary = parts[1]
                
                # Create a meaning for this topic
                meanings.append(
                    Meaning(
                        base=i+1,  # Use topic index as base
                        position=i+1,  # Use topic index as position
                        value=i+3,  # Some arbitrary value
                        heading=f"{primary} related to {secondary}",
                        meaning=f"Based on your birth chart, your {self.CATEGORY_MAPPINGS.get(primary, {}).get('thai_meaning', primary)} is influenced by {self.CATEGORY_MAPPINGS.get(secondary, {}).get('thai_meaning', secondary)}. This indicates that...",
                        category=f"{primary}-{secondary}",
                        match_score=9.0 - i  # First topic gets highest score
                    )
                )
        
        # Add some generic readings
        base_names = ["Base 1 (Day)", "Base 2 (Month)", "Base 3 (Year)", "Base 4 (Sum)"]
        for base in range(1, 5):
            for position in range(1, 4):  # Add 3 positions per base
                if len(meanings) >= 15:  # Limit total meanings
                    break
                    
                meanings.append(
                    Meaning(
                        base=base,
                        position=position,
                        value=position,
                        heading=f"{base_names[base-1]} Position {position}",
                        meaning=f"This represents your {['personality', 'finances', 'relationships', 'future'][position % 4]} and indicates that...",
                        category="General",
                        match_score=5.0 - base - position  # Lower priority than topic-specific meanings
                    )
                )
        
        # Sort by match score
        meanings.sort(key=lambda m: getattr(m, 'match_score', 0), reverse=True)
        
        # Create collection
        result = MeaningCollection(items=meanings)
        
        # Cache result
        self._meaning_cache[cache_key] = result
        
        return result

# Mock calculator service
class MockCalculatorService:
    """Mock calculator service for generating birth bases"""
    
    def calculate_birth_bases(self, birth_date, thai_day):
        """Calculate mock birth bases"""
        # Create test birth info
        birth_info = BirthInfo(
            date=birth_date,
            day=thai_day,
            day_value=3,
            month=birth_date.month,
            year_animal="Horse",  # English translation
            year_start_number=7
        )
        
        # Create test bases
        bases = Bases(
            base1=[1, 2, 3, 4, 5, 6, 7],
            base2=[3, 4, 5, 6, 7, 1, 2],
            base3=[5, 6, 7, 1, 2, 3, 4],
            base4=[7, 1, 2, 3, 4, 5, 6]
        )
        
        # Create bases result
        return BasesResult(
            bases=bases,
            birth_info=birth_info
        )

async def test_meaning_extraction_mock():
    """Test the meaning extraction functionality with mocks"""
    logger.info("Testing mock meaning extraction functionality...")
    
    try:
        # Initialize mock services
        meaning_service = MockMeaningService()
        calculator_service = MockCalculatorService()
        
        # Create test birth info and calculate bases
        birth_date = datetime.now()
        thai_day = "Monday"  # Use English instead of Thai
        
        # Calculate bases
        bases_result = calculator_service.calculate_birth_bases(birth_date, thai_day)
        bases = bases_result.bases
        
        logger.info(f"Calculated mock bases for birth date {birth_date}, day {thai_day}")
        
        # Test questions with English translations
        test_questions = [
            "ฉันจะมีความรักที่ดีเมื่อไหร่",  # When will I have good love?
            "การเงินของฉันในปีนี้จะเป็นอย่างไร",  # How will my finances be this year?
            "อาชีพของฉันจะก้าวหน้าหรือไม่",  # Will my career progress?
            "สุขภาพของฉันในอนาคตจะเป็นอย่างไร",  # How will my health be in the future?
            "การเรียนของลูกฉันจะเป็นอย่างไร",  # How will my child's education be?
        ]
        
        # English translations for logging
        translations = [
            "When will I have good love?",
            "How will my finances be this year?",
            "Will my career progress?",
            "How will my health be in the future?",
            "How will my child's education be?"
        ]
        
        extraction_results = {}
        
        # Extract meanings for each question
        for i, question in enumerate(test_questions):
            try:
                logger.info(f"Extracting meanings for question {i+1}: '{translations[i]}'")
                
                # First identify topics with AI
                start_time_topics = datetime.now()
                topics = await meaning_service._identify_topics_with_ai(question)
                end_time_topics = datetime.now()
                topic_duration = (end_time_topics - start_time_topics).total_seconds()
                
                logger.info(f"Identified topics: {topics}")
                logger.info(f"Topic identification duration: {topic_duration:.2f} seconds")
                
                # Then extract meanings based on the topics
                start_time_meanings = datetime.now()
                meanings = await meaning_service.extract_meanings(bases, question)
                end_time_meanings = datetime.now()
                meaning_duration = (end_time_meanings - start_time_meanings).total_seconds()
                
                logger.info(f"Extracted {len(meanings.items)} meanings")
                logger.info(f"Meaning extraction duration: {meaning_duration:.2f} seconds")
                
                # Test caching
                start_time_cached = datetime.now()
                cached_meanings = await meaning_service.extract_meanings(bases, question)
                end_time_cached = datetime.now()
                cached_duration = (end_time_cached - start_time_cached).total_seconds()
                
                logger.info(f"Retrieved {len(cached_meanings.items)} meanings from cache")
                logger.info(f"Cached retrieval duration: {cached_duration:.2f} seconds")
                
                # Record the top meanings
                top_meanings = []
                for meaning in meanings.items[:3]:  # Get top 3 meanings
                    top_meanings.append({
                        "base": meaning.base,
                        "position": meaning.position,
                        "value": meaning.value,
                        "heading": meaning.heading,
                        "category": meaning.category,
                        "match_score": getattr(meaning, 'match_score', 0),
                        "meaning_preview": meaning.meaning[:100] + "..." if len(meaning.meaning) > 100 else meaning.meaning
                    })
                
                # Store the results
                extraction_results[f"Question {i+1}"] = {
                    "translation": translations[i],
                    "topics": topics,
                    "topic_identification_duration": topic_duration,
                    "meanings_count": len(meanings.items),
                    "meaning_extraction_duration": meaning_duration,
                    "cached_retrieval_duration": cached_duration,
                    "top_meanings": top_meanings
                }
                
                logger.info("-" * 80)
                
            except Exception as e:
                logger.error(f"Error extracting meanings for question {i+1}: {str(e)}", exc_info=True)
        
        # Generate report
        print("\n=== Meaning Extraction Test Results ===")
        print(f"Tested {len(test_questions)} questions")
        
        total_topic_duration = sum(result["topic_identification_duration"] for result in extraction_results.values())
        total_meaning_duration = sum(result["meaning_extraction_duration"] for result in extraction_results.values())
        total_cached_duration = sum(result["cached_retrieval_duration"] for result in extraction_results.values())
        total_meanings = sum(result["meanings_count"] for result in extraction_results.values())
        
        print(f"\nTotal meanings extracted: {total_meanings}")
        print(f"Average meanings per question: {total_meanings / len(extraction_results):.2f}")
        print(f"Average topic identification time: {total_topic_duration / len(extraction_results):.2f} seconds")
        print(f"Average meaning extraction time: {total_meaning_duration / len(extraction_results):.2f} seconds")
        print(f"Average cached retrieval time: {total_cached_duration / len(extraction_results):.2f} seconds")
        
        # Calculate improvement safely
        if total_meaning_duration > 0:
            improvement = ((total_meaning_duration - total_cached_duration) / total_meaning_duration * 100)
        else:
            improvement = 0
            
        print(f"Caching speed improvement: {improvement:.2f}%")
        
        print("\n--- Top Meanings by Question ---")
        for q_id, result in extraction_results.items():
            print(f"\n{q_id}: '{result['translation']}'")
            print(f"Topics: {result['topics']}")
            
            for i, meaning in enumerate(result["top_meanings"]):
                print(f"\n  Top Meaning {i+1}:")
                print(f"    Base: {meaning['base']}, Position: {meaning['position']}, Value: {meaning['value']}")
                print(f"    Heading: {meaning['heading']}")
                print(f"    Category: {meaning['category']}")
                print(f"    Match Score: {meaning['match_score']}")
                print(f"    Preview: {meaning['meaning_preview']}")
        
        # Save results to file for analysis
        with open("meaning_extraction_mock_results.json", "w", encoding="utf-8") as f:
            json.dump(extraction_results, f, ensure_ascii=False, indent=2)
        logger.info("Saved results to meaning_extraction_mock_results.json")
        
        # Test successful if caching improved performance
        caching_improved = total_cached_duration < total_meaning_duration * 0.5
        return caching_improved
        
    except Exception as e:
        logger.error(f"Error testing meaning extraction: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        # Run the async test
        success = asyncio.run(test_meaning_extraction_mock())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1) 