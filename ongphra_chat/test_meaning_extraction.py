#!/usr/bin/env python
# test_meaning_extraction.py
"""
Test script specifically for meaning extraction functionality based on AI topic identification
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
logger = logging.getLogger("test_meaning_extraction")
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


async def test_meaning_extraction():
    """Test the meaning extraction functionality"""
    logger.info("Testing meaning extraction functionality...")
    
    try:
        # Initialize repositories and services
        logger.info("Initializing repositories and services...")
        category_repository = CategoryRepository()
        reading_repository = ReadingRepository()
        meaning_service = MeaningService(
            category_repository=category_repository,
            reading_repository=reading_repository
        )
        calculator_service = CalculatorService()
        
        # Create a test birth info and calculate bases
        birth_date = datetime(1990, 5, 15)  # May 15, 1990
        thai_day = "อังคาร"  # Tuesday
        
        # Calculate bases
        bases_result = calculator_service.calculate_birth_bases(birth_date, thai_day)
        bases = bases_result.bases
        
        logger.info(f"Calculated bases for birth date {birth_date}, Thai day {thai_day}")
        
        # Test questions covering different domains
        test_questions = [
            "ฉันจะมีความรักที่ดีเมื่อไหร่",  # Love
            "การเงินของฉันในปีนี้จะเป็นอย่างไร",  # Finance
            "อาชีพของฉันจะก้าวหน้าหรือไม่",  # Career
            "สุขภาพของฉันในอนาคตจะเป็นอย่างไร",  # Health
            "การเรียนของลูกฉันจะเป็นอย่างไร",  # Education
        ]
        
        extraction_results = {}
        
        # Extract meanings for each question
        for question in test_questions:
            try:
                logger.info(f"Extracting meanings for question: '{question}'")
                
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
                extraction_results[question] = {
                    "topics": topics,
                    "topic_identification_duration": topic_duration,
                    "meanings_count": len(meanings.items),
                    "meaning_extraction_duration": meaning_duration,
                    "top_meanings": top_meanings
                }
                
                logger.info("-" * 80)
                
            except Exception as e:
                logger.error(f"Error extracting meanings for question '{question}': {str(e)}", exc_info=True)
        
        # Generate report
        print("\n=== Meaning Extraction Test Results ===")
        print(f"Tested {len(test_questions)} questions")
        
        total_topic_duration = sum(result["topic_identification_duration"] for result in extraction_results.values())
        total_meaning_duration = sum(result["meaning_extraction_duration"] for result in extraction_results.values())
        total_meanings = sum(result["meanings_count"] for result in extraction_results.values())
        
        print(f"\nTotal meanings extracted: {total_meanings}")
        print(f"Average meanings per question: {total_meanings / len(extraction_results):.2f}")
        print(f"Average topic identification time: {total_topic_duration / len(extraction_results):.2f} seconds")
        print(f"Average meaning extraction time: {total_meaning_duration / len(extraction_results):.2f} seconds")
        
        print("\n--- Top Meanings by Question ---")
        for question, result in extraction_results.items():
            print(f"\nQuestion: '{question}'")
            print(f"Topics: {result['topics']}")
            
            for i, meaning in enumerate(result["top_meanings"]):
                print(f"\n  Top Meaning {i+1}:")
                print(f"    Base: {meaning['base']}, Position: {meaning['position']}, Value: {meaning['value']}")
                print(f"    Heading: {meaning['heading']}")
                print(f"    Category: {meaning['category']}")
                print(f"    Match Score: {meaning['match_score']}")
                print(f"    Preview: {meaning['meaning_preview']}")
        
        # Save results to file for analysis
        with open("meaning_extraction_results.json", "w", encoding="utf-8") as f:
            json.dump(extraction_results, f, ensure_ascii=False, indent=2)
        logger.info("Saved results to meaning_extraction_results.json")
        
        # Perform full birth chart test
        print("\n=== Full Birth Chart Test ===")
        logger.info("Testing full birth chart generation with focus question...")
        
        start_time = datetime.now()
        focus_question = "ฉันควรทำอย่างไรกับงานในอนาคต"  # Career-focused question
        enriched_chart = await meaning_service.get_enriched_birth_chart(
            birth_date=birth_date,
            thai_day=thai_day,
            question=focus_question
        )
        end_time = datetime.now()
        chart_duration = (end_time - start_time).total_seconds()
        
        # Extract metrics
        total_general_meanings = sum(len(base_data["meanings"]) for base_data in enriched_chart["general_meanings"].values())
        focus_meanings_count = len(enriched_chart["focus_meanings"])
        
        print(f"Birth chart generated in {chart_duration:.2f} seconds")
        print(f"Total general meanings: {total_general_meanings}")
        print(f"Focus meanings related to question: {focus_meanings_count}")
        
        if focus_meanings_count > 0:
            print("\n--- Top Focus Meanings ---")
            for i, meaning in enumerate(enriched_chart["focus_meanings"][:3]):
                print(f"\n  Focus Meaning {i+1}:")
                print(f"    Base: {meaning['base']}, Position: {meaning['position']}, Value: {meaning['value']}")
                print(f"    Heading: {meaning['heading']}")
                print(f"    Category: {meaning['category']}")
                print(f"    Match Score: {meaning['match_score']}")
                print(f"    Preview: {meaning['meaning'][:100]}..." if len(meaning['meaning']) > 100 else meaning['meaning'])
        
        # Save birth chart to file
        with open("test_birth_chart_result.json", "w", encoding="utf-8") as f:
            json.dump(enriched_chart, f, ensure_ascii=False, indent=2)
        logger.info("Saved birth chart to test_birth_chart_result.json")
        
    except Exception as e:
        logger.error(f"Error testing meaning extraction: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        # Run the async test
        asyncio.run(test_meaning_extraction())
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1) 