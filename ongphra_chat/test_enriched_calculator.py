#!/usr/bin/env python
# test_enriched_calculator.py
"""
Test script to demonstrate enriching calculator results with category details from database
"""
import os
import sys
import json
import asyncio
from datetime import datetime
from pprint import pprint

# Adjust Python path to find app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

async def get_enriched_calculator_results():
    """Enrich calculator results with category details from database"""
    try:
        # Import necessary modules
        from app.repository.category_repository import CategoryRepository
        from app.services.calculator import CalculatorService
        
        # Initialize services
        calculator = CalculatorService()
        category_repository = CategoryRepository()
        
        # Test data
        birth_date = datetime(1990, 5, 15)  # May 15, 1990
        thai_day = "อังคาร"  # Tuesday
        
        print(f"Calculating bases for birth_date={birth_date}, thai_day={thai_day}")
        
        # Calculate bases
        result = calculator.calculate_birth_bases(birth_date, thai_day)
        
        # Get Thai position names
        day_labels = calculator.day_labels
        month_labels = calculator.month_labels
        year_labels = calculator.year_labels
        
        # Create a mapping of bases to their labels
        base_labels = {
            1: day_labels,
            2: month_labels,
            3: year_labels
        }
        
        # Create enriched result
        enriched_result = {
            "birth_info": {
                "date": birth_date.isoformat(),
                "day": result.birth_info.day,
                "day_value": result.birth_info.day_value,
                "month": result.birth_info.month,
                "year_animal": result.birth_info.year_animal,
                "year_start_number": result.birth_info.year_start_number
            },
            "bases": {}
        }
        
        # Enrich each base with category details
        for base_num in range(1, 5):
            base_key = f"base{base_num}"
            base_values = getattr(result.bases, base_key)
            
            enriched_positions = []
            
            for position, value in enumerate(base_values):
                position_num = position + 1  # Convert to 1-indexed for display
                
                # Get the Thai position name
                thai_position_name = ""
                if base_num < 4 and position < len(base_labels[base_num]):
                    thai_position_name = base_labels[base_num][position]
                
                # Create position data
                position_data = {
                    "position": position_num,
                    "value": value,
                    "name": thai_position_name
                }
                
                # If we have a position name, query the database for details
                if thai_position_name:
                    category = await category_repository.get_by_name(thai_position_name)
                    
                    if category:
                        position_data.update({
                            "category_id": category.id,
                            "thai_meaning": category.thai_meaning if hasattr(category, 'thai_meaning') else "",
                            "house_number": category.house_number if hasattr(category, 'house_number') else None,
                            "house_type": category.house_type if hasattr(category, 'house_type') else "",
                            "found_in_db": True
                        })
                    else:
                        position_data.update({
                            "category_id": None, 
                            "thai_meaning": f"ไม่พบความหมายของ {thai_position_name} ในฐานข้อมูล",
                            "house_number": None,
                            "house_type": "",
                            "found_in_db": False
                        })
                
                enriched_positions.append(position_data)
            
            enriched_result["bases"][base_key] = enriched_positions
        
        # Save to file for inspection
        with open("enriched_calculator_result.json", "w", encoding="utf-8") as f:
            json.dump(enriched_result, f, ensure_ascii=False, indent=2)
        print("Saved result to enriched_calculator_result.json")
        
        # Print some summary information
        print("\n=== Enriched Base Summary ===")
        
        for base_num in range(1, 5):
            base_key = f"base{base_num}"
            positions = enriched_result["bases"][base_key]
            
            print(f"\n--- Base {base_num} ---")
            for pos in positions:
                if "thai_meaning" in pos and pos["thai_meaning"]:
                    meaning = pos["thai_meaning"]
                    print(f"Position {pos['position']} ({pos['name']}): Value={pos['value']}, Meaning='{meaning}'")
                else:
                    print(f"Position {pos['position']} ({pos['name']}): Value={pos['value']}")
        
        return enriched_result
    
    except Exception as e:
        print(f"Error enriching calculator results: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the async function
    result = asyncio.run(get_enriched_calculator_results())
    
    if result:
        print("\nEnriched calculator test completed successfully!")
    else:
        print("\nEnriched calculator test failed!")
        sys.exit(1) 