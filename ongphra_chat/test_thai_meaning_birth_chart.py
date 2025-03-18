#!/usr/bin/env python
# test_thai_meaning_birth_chart.py
"""
Test script for the enriched birth chart with Thai meanings
"""
import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_thai_meaning_birth_chart")

# Adjust Python path to find app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    # Import all necessary classes first to ensure they're in scope
    logger.info("Importing necessary modules")
    from app.domain.bases import BasesResult
    from app.domain.meaning import MeaningCollection, Meaning
    from app.services.calculator import CalculatorService
    from app.repository.category_repository import CategoryRepository
    from app.repository.reading_repository import ReadingRepository
    from app.services.meaning import MeaningService
    
    logger.info("Imports completed successfully")
except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    print(f"Failed to import necessary modules: {str(e)}")
    sys.exit(1)

async def test_thai_meaning_birth_chart():
    """Test the enriched birth chart that includes Thai meanings for AI"""
    try:
        # Initialize repositories and service
        category_repository = CategoryRepository()
        reading_repository = ReadingRepository()
        meaning_service = MeaningService(
            category_repository=category_repository,
            reading_repository=reading_repository
        )
        
        # Test data
        birth_date = datetime(1990, 5, 15)  # May 15, 1990
        thai_day = "อังคาร"  # Tuesday
        question = "ฉันควรทำอย่างไรกับงานในอนาคต"  # "What should I do with my future career?"
        
        print(f"Testing enriched birth chart with Thai meanings for birth_date={birth_date}, thai_day={thai_day}")
        
        # Get enriched birth chart
        result = await meaning_service.get_enriched_birth_chart(
            birth_date=birth_date,
            thai_day=thai_day,
            question=question
        )
        
        # Save the result to a file for inspection
        with open("thai_meaning_birth_chart.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("Saved result to thai_meaning_birth_chart.json")
        
        # Print the positions summary for AI reference
        print("\n=== Positions Summary for AI ===")
        for position_name, details in result["positions_summary"].items():
            print(f"{position_name}: {details['thai_meaning']} (Base {details['base']}, Value {details['value']})")
        
        # Print some focus meanings if available
        if result["focus_meanings"]:
            print("\n=== Focus Meanings (First 3) ===")
            for i, meaning in enumerate(result["focus_meanings"][:3]):
                print(f"\n--- Focus Meaning {i+1} ---")
                print(f"Heading: {meaning['heading']}")
                print(f"Category: {meaning['category']}")
                print(f"Base: {meaning['base']}, Position: {meaning['position']}, Value: {meaning['value']}")
                print(f"Match Score: {meaning.get('match_score', 'N/A')}")
                meaning_text = meaning.get('meaning', '')
                print(f"Meaning: {meaning_text[:100]}..." if len(meaning_text) > 100 else f"Meaning: {meaning_text}")
        
        # Print the enriched bases (first few positions from each base)
        print("\n=== Enriched Bases (Sample) ===")
        for base_num in range(1, 4):
            base_key = f"base{base_num}"
            if base_key in result["enriched_bases"]:
                positions = result["enriched_bases"][base_key][:2]  # First 2 positions from each base
                
                print(f"\n--- Base {base_num} (First 2 Positions) ---")
                for pos in positions:
                    if "thai_meaning" in pos and pos["thai_meaning"]:
                        print(f"Position {pos['position']} ({pos['name']}): Value={pos['value']}, Meaning='{pos['thai_meaning']}'")
                    else:
                        print(f"Position {pos['position']} ({pos.get('name', '')}): Value={pos['value']}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error testing Thai meaning birth chart: {str(e)}", exc_info=True)
        print(f"Error testing Thai meaning birth chart: {str(e)}")
        return None

if __name__ == "__main__":
    # Run the async function
    result = asyncio.run(test_thai_meaning_birth_chart())
    
    if result:
        print("\nThai meaning birth chart test completed successfully!")
    else:
        print("\nThai meaning birth chart test failed!")
        sys.exit(1) 