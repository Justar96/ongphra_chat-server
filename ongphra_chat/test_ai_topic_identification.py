#!/usr/bin/env python
# test_ai_topic_identification.py
"""
Test script specifically for AI topic identification functionality
"""
import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_ai_topic_identification")
logger.setLevel(logging.DEBUG)

# Add the parent directory to path to find the app modules
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)
logger.info(f"Added {parent_dir} to Python path")

try:
    # Import necessary modules
    logger.info("Importing modules...")
    from app.repository.category_repository import CategoryRepository
    from app.repository.reading_repository import ReadingRepository
    from app.services.meaning import MeaningService
    from app.services.calculator import CalculatorService
    logger.info("Modules imported successfully")
except Exception as e:
    logger.error(f"Error importing modules: {str(e)}", exc_info=True)
    sys.exit(1)


async def test_ai_topic_identification():
    """Test the AI topic identification functionality"""
    logger.info("Testing AI topic identification functionality...")
    
    try:
        # Initialize repositories and services
        logger.info("Initializing repositories and services...")
        category_repository = CategoryRepository()
        reading_repository = ReadingRepository()
        meaning_service = MeaningService(
            category_repository=category_repository,
            reading_repository=reading_repository
        )
        
        # Test questions covering different domains
        test_questions = [
            "ฉันจะมีความรักที่ดีเมื่อไหร่",  # Love
            "การเงินของฉันในปีนี้จะเป็นอย่างไร",  # Finance
            "อาชีพของฉันจะก้าวหน้าหรือไม่",  # Career
            "สุขภาพของฉันในอนาคตจะเป็นอย่างไร",  # Health
            "ครอบครัวของฉันจะมีความสุขหรือไม่",  # Family
            "ฉันควรย้ายบ้านในปีนี้หรือไม่",  # Housing/Relocation
            "การเรียนของลูกฉันจะเป็นอย่างไร",  # Education
            "ฉันจะได้รับโชคลาภเมื่อไหร่",  # Fortune/Luck
            "ฉันจะได้เดินทางไปต่างประเทศหรือไม่",  # Travel
            "อนาคตของฉันจะเป็นอย่างไร"  # General future
        ]
        
        results = {}
        cached_results = {}
        
        # First round - initial identification
        logger.info("First round - testing initial topic identification...")
        for question in test_questions:
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
                
                logger.info(f"Question: '{question}'")
                logger.info(f"Identified topics: {topics}")
                logger.info(f"Duration: {duration:.2f} seconds")
                logger.info("-" * 80)
                
            except Exception as e:
                logger.error(f"Error identifying topics for question '{question}': {str(e)}", exc_info=True)
        
        # Second round - to test caching
        logger.info("\nSecond round - testing caching functionality...")
        for question in test_questions:
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
                
                logger.info(f"Question: '{question}'")
                logger.info(f"Identified topics: {topics}")
                logger.info(f"Duration: {duration:.2f} seconds")
                logger.info("-" * 80)
                
            except Exception as e:
                logger.error(f"Error identifying topics for question '{question}': {str(e)}", exc_info=True)
        
        # Compare results and generate report
        logger.info("\nResults comparison:")
        print("\n=== AI Topic Identification Test Results ===")
        print(f"Tested {len(test_questions)} questions")
        
        print("\n--- Topic Consistency Check ---")
        consistency_failures = 0
        for question in test_questions:
            if question in results and question in cached_results:
                topics1 = sorted(results[question]["topics"])
                topics2 = sorted(cached_results[question]["topics"])
                
                is_consistent = topics1 == topics2
                
                print(f"Question: '{question}'")
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
        print(f"Performance improvement: {((first_round_avg - second_round_avg) / first_round_avg * 100):.2f}%")
        
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
            print("✅ All topic identifications are consistent between runs")
        else:
            print(f"❌ Found {consistency_failures} consistency failures")
            
        if second_round_avg < first_round_avg * 0.1:  # If cached response is less than 10% of original time
            print("✅ Caching is working effectively")
        else:
            print("❌ Caching may not be working effectively")
        
        # Save results to file for analysis
        output = {
            "first_round": results,
            "second_round": cached_results,
            "summary": {
                "first_round_avg": first_round_avg,
                "second_round_avg": second_round_avg,
                "improvement_percentage": ((first_round_avg - second_round_avg) / first_round_avg * 100),
                "consistency_failures": consistency_failures,
                "most_common_topics": {topic: count for topic, count in sorted_topics[:5]}
            }
        }
        
        with open("ai_topic_identification_results.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info("Saved results to ai_topic_identification_results.json")
        
    except Exception as e:
        logger.error(f"Error testing AI topic identification: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        # Run the async test
        asyncio.run(test_ai_topic_identification())
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1) 