#!/usr/bin/env python
# test_ai_topic_identification_mock.py
"""
Test script specifically for AI topic identification functionality using mock repositories
"""
import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from pprint import pprint

# Fix encoding issues for Windows console
if sys.platform == 'win32':
    # Set UTF-8 mode for Python 3.7+ Windows
    try:
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32')
        kernel32.SetConsoleOutputCP(65001)  # Set console output to UTF-8
    except Exception as e:
        print(f"Warning: Could not set console mode: {e}")

# Configure logging
try:
    # Create custom handler with encoding specified
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Configure logger with our handler
    logger = logging.getLogger("test_ai_topic_identification_mock")
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # Avoid propagation to root logger to prevent duplicate messages
    logger.propagate = False
except Exception as e:
    print(f"Warning: Logger setup error: {e}")
    # Fallback basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("test_ai_topic_identification_mock")

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

async def test_ai_topic_identification_mock():
    """Test the AI topic identification functionality with mocks"""
    logger.info("Testing mock AI topic identification functionality...")
    
    try:
        # Initialize mock service
        meaning_service = MockMeaningService()
        
        # Test questions covering different domains with English translations
        test_questions = [
            "ฉันจะมีความรักที่ดีเมื่อไหร่",  # When will I have good love?
            "การเงินของฉันในปีนี้จะเป็นอย่างไร",  # How will my finances be this year?
            "อาชีพของฉันจะก้าวหน้าหรือไม่",  # Will my career progress?
            "สุขภาพของฉันในอนาคตจะเป็นอย่างไร",  # How will my health be in the future?
            "ครอบครัวของฉันจะมีความสุขหรือไม่",  # Will my family be happy?
            "ฉันควรย้ายบ้านในปีนี้หรือไม่",  # Should I move house this year?
            "การเรียนของลูกฉันจะเป็นอย่างไร",  # How will my child's education be?
            "ฉันจะได้รับโชคลาภเมื่อไหร่",  # When will I receive fortune?
            "ฉันจะได้เดินทางไปต่างประเทศหรือไม่",  # Will I travel abroad?
            "อนาคตของฉันจะเป็นอย่างไร"  # How will my future be?
        ]
        
        # Create mapping from Thai questions to English translations for logging
        translations = [
            "When will I have good love?",
            "How will my finances be this year?",
            "Will my career progress?",
            "How will my health be in the future?",
            "Will my family be happy?",
            "Should I move house this year?",
            "How will my child's education be?",
            "When will I receive fortune?",
            "Will I travel abroad?",
            "How will my future be?"
        ]
        
        results = {}
        cached_results = {}
        
        # First round - initial identification
        logger.info("First round - testing initial topic identification...")
        for i, question in enumerate(test_questions):
            try:
                start_time = datetime.now()
                topics = await meaning_service._identify_topics_with_ai(question)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                # Store the results
                results[question] = {
                    "topics": topics,
                    "duration": duration
                }
                
                logger.info(f"Question {i+1}: '{translations[i]}'")
                logger.info(f"Identified topics: {topics}")
                logger.info(f"Duration: {duration:.2f} seconds")
                logger.info("-" * 80)
                
            except Exception as e:
                logger.error(f"Error identifying topics for Question {i+1}: {str(e)}", exc_info=True)
        
        # Second round - to test caching
        logger.info("\nSecond round - testing caching functionality...")
        for i, question in enumerate(test_questions):
            try:
                start_time = datetime.now()
                topics = await meaning_service._identify_topics_with_ai(question)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                # Store the results
                cached_results[question] = {
                    "topics": topics,
                    "duration": duration
                }
                
                logger.info(f"Question {i+1}: '{translations[i]}' (cached)")
                logger.info(f"Identified topics: {topics}")
                logger.info(f"Duration: {duration:.2f} seconds")
                logger.info("-" * 80)
                
            except Exception as e:
                logger.error(f"Error identifying topics for Question {i+1}: {str(e)}", exc_info=True)
        
        # Compare results and generate report
        logger.info("\nResults comparison:")
        print("\n=== AI Topic Identification Test Results ===")
        print(f"Tested {len(test_questions)} questions")
        
        print("\n--- Topic Consistency Check ---")
        consistency_failures = 0
        for i, question in enumerate(test_questions):
            if question in results and question in cached_results:
                topics1 = sorted(results[question]["topics"])
                topics2 = sorted(cached_results[question]["topics"])
                
                is_consistent = topics1 == topics2
                
                print(f"Question {i+1}: '{translations[i]}'")
                print(f"  Initial topics: {topics1}")
                print(f"  Cached topics:  {topics2}")
                print(f"  Consistent: {'Yes' if is_consistent else 'No - FAILURE'}")
                
                if not is_consistent:
                    consistency_failures += 1
        
        print("\n--- Performance Check ---")
        first_round_avg = sum(result["duration"] for result in results.values()) / len(results)
        second_round_avg = sum(result["duration"] for result in cached_results.values()) / len(cached_results)
        
        print(f"First round average duration: {first_round_avg:.2f} seconds")
        print(f"Second round average duration: {second_round_avg:.2f} seconds")
        
        # Calculate improvement safely
        if first_round_avg > 0:
            improvement = ((first_round_avg - second_round_avg) / first_round_avg * 100)
        else:
            improvement = 0
            
        print(f"Performance improvement: {improvement:.2f}%")
        
        print("\n--- Topic Pair Analysis ---")
        # Collect all topics
        all_topics = []
        for result in results.values():
            all_topics.extend(result["topics"])
        
        # Count occurrences
        topic_counts = {}
        for topic in all_topics:
            if topic in topic_counts:
                topic_counts[topic] += 1
            else:
                topic_counts[topic] = 1
        
        # Sort by frequency
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        
        print("Most common topic pairs:")
        for topic, count in sorted_topics[:5]:
            print(f"  {topic}: {count} occurrences")
        
        # Overall test result
        print("\n--- Test Results Summary ---")
        if consistency_failures == 0:
            print("[SUCCESS] All topic identifications are consistent between runs")
        else:
            print(f"[FAILURE] Found {consistency_failures} consistency failures")
            
        if second_round_avg < first_round_avg * 0.5:  # If cached response is less than 50% of original time
            print("[SUCCESS] Caching is working effectively")
        else:
            print("[FAILURE] Caching may not be working effectively")
        
        # Save results to file for analysis
        output = {
            "summary": {
                "first_round_avg": first_round_avg,
                "second_round_avg": second_round_avg,
                "improvement_percentage": improvement,
                "consistency_failures": consistency_failures,
                "most_common_topics": {topic: count for topic, count in sorted_topics[:5]}
            }
        }
        
        # Don't include Thai text in JSON
        first_round_results = {}
        second_round_results = {}
        
        for i, question in enumerate(test_questions):
            first_round_results[f"Question {i+1}"] = results[question]
            second_round_results[f"Question {i+1}"] = cached_results[question]
        
        output["first_round"] = first_round_results
        output["second_round"] = second_round_results
        
        with open("ai_topic_identification_mock_results.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info("Saved results to ai_topic_identification_mock_results.json")
        
        return consistency_failures == 0 and second_round_avg < first_round_avg * 0.5
        
    except Exception as e:
        logger.error(f"Error testing AI topic identification: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        # Run the async test
        success = asyncio.run(test_ai_topic_identification_mock())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1) 