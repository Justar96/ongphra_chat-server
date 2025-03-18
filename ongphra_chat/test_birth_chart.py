#!/usr/bin/env python
# test_birth_chart.py
"""
Simple test script to verify the enriched birth chart functionality
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
logger = logging.getLogger("test_birth_chart")
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


async def test_enriched_birth_chart():
    """Test the enriched birth chart functionality"""
    logger.info("Testing enriched birth chart functionality...")
    
    try:
        # Initialize repositories and services
        logger.info("Initializing repositories and services...")
        category_repository = CategoryRepository()
        reading_repository = ReadingRepository()
        meaning_service = MeaningService(
            category_repository=category_repository,
            reading_repository=reading_repository
        )
        
        # Test data
        birth_date = datetime(1990, 5, 15)  # May 15, 1990
        thai_day = "อังคาร"  # Tuesday
        question = "ฉันควรทำอย่างไรกับงานในอนาคต" # "What should I do with my future career?"
        
        logger.info(f"Using test data: birth_date={birth_date}, thai_day={thai_day}, question={question}")
        
        # Get enriched birth chart
        logger.info("Getting enriched birth chart...")
        enriched_chart = await meaning_service.get_enriched_birth_chart(
            birth_date=birth_date,
            thai_day=thai_day,
            question=question
        )
        
        # Print the result (formatted as JSON)
        logger.info("Enriched birth chart generated successfully")
        
        # Save to file for inspection
        with open("enriched_chart_result.json", "w", encoding="utf-8") as f:
            json.dump(enriched_chart, f, ensure_ascii=False, indent=2)
        logger.info("Saved result to enriched_chart_result.json")
        
        print("\n=== Enriched Birth Chart Generated ===")
        print("Full result saved to enriched_chart_result.json")
        
        # Print some key sections
        print("\n=== Birth Info ===")
        pprint(enriched_chart["birth_info"])
        
        print("\n=== Base 1 (Day) ===")
        pprint(enriched_chart["enriched_bases"]["base1"][:2])  # First 2 positions
        
        print("\n=== Focus Meanings ===")
        print(f"Total: {len(enriched_chart['focus_meanings'])}")
        if enriched_chart["focus_meanings"]:
            for i, meaning in enumerate(enriched_chart["focus_meanings"][:2]):
                print(f"\n--- Focused Meaning {i+1} ---")
                print(f"Heading: {meaning['heading']}")
                print(f"Base: {meaning['base']}, Position: {meaning['position']}, Value: {meaning['value']}")
                print(f"Category: {meaning['category']}")
                print(f"Match Score: {meaning['match_score']}")
                print(f"Meaning: {meaning['meaning'][:100]}...")  # First 100 chars
        
        print("\n=== General Meanings ===")
        total_meanings = sum(len(base_data["meanings"]) for base_data in enriched_chart["general_meanings"].values())
        print(f"Total: {total_meanings}")
        
        for base_key, base_data in enriched_chart["general_meanings"].items():
            print(f"\n--- {base_data['name']} ({base_key}) ---")
            meanings = base_data["meanings"]
            if meanings:
                for i, meaning in enumerate(meanings[:2]):  # Show first 2 meanings per base
                    print(f"\nMeaning {i+1}:")
                    print(f"Heading: {meaning['heading']}")
                    print(f"Position: {meaning['position']}, Value: {meaning['value']}")
                    print(f"Category: {meaning['category']}")
                    print(f"Match Score: {meaning.get('match_score', 'N/A')}")
                    print(f"Meaning: {meaning['meaning'][:100]}...")  # First 100 chars
                
    except Exception as e:
        logger.error(f"Error testing enriched birth chart: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        # Run the async test
        asyncio.run(test_enriched_birth_chart())
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1) 