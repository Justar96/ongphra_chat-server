#!/usr/bin/env python
# test_database_categories.py
"""
Test script to retrieve category details from the database for calculator positions
"""
import os
import sys
import asyncio
from datetime import datetime
from pprint import pprint

# Adjust Python path to find app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

async def get_categories_for_positions():
    """Retrieve category details from database for calculator positions"""
    try:
        # Import necessary modules
        from app.repository.category_repository import CategoryRepository
        from app.services.calculator import CalculatorService
        
        # Create calculator to get position names
        calculator = CalculatorService()
        day_labels = calculator.day_labels
        month_labels = calculator.month_labels
        year_labels = calculator.year_labels
        
        # Initialize repository
        category_repository = CategoryRepository()
        
        # Combined list of all position names
        all_positions = day_labels + month_labels + year_labels
        
        print(f"Retrieving details for {len(all_positions)} positions from database...")
        
        # Create a dictionary to hold results
        position_details = {}
        
        # Query each position
        for position_name in all_positions:
            # Get category by name
            category = await category_repository.get_by_name(position_name)
            
            if category:
                position_details[position_name] = {
                    "id": category.id,
                    "name": category.name,
                    "thai_meaning": category.thai_meaning if hasattr(category, 'thai_meaning') else "",
                    "house_number": category.house_number if hasattr(category, 'house_number') else None,
                    "house_type": category.house_type if hasattr(category, 'house_type') else ""
                }
                print(f"Found category for {position_name}: {position_details[position_name]}")
            else:
                position_details[position_name] = {
                    "id": None,
                    "name": position_name,
                    "thai_meaning": "",
                    "house_number": None,
                    "house_type": ""
                }
                print(f"No category found for {position_name}")
        
        # Print summary
        print("\n=== Category Details ===")
        
        print("\n--- Day Positions ---")
        for position in day_labels:
            details = position_details.get(position, {})
            print(f"{position}: Thai meaning = '{details.get('thai_meaning', '')}', House = {details.get('house_number', 'None')}")
        
        print("\n--- Month Positions ---")
        for position in month_labels:
            details = position_details.get(position, {})
            print(f"{position}: Thai meaning = '{details.get('thai_meaning', '')}', House = {details.get('house_number', 'None')}")
        
        print("\n--- Year Positions ---")
        for position in year_labels:
            details = position_details.get(position, {})
            print(f"{position}: Thai meaning = '{details.get('thai_meaning', '')}', House = {details.get('house_number', 'None')}")
        
        return position_details
    
    except Exception as e:
        print(f"Error retrieving categories: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the async function
    result = asyncio.run(get_categories_for_positions())
    
    if result:
        print("\nDatabase query completed successfully!")
    else:
        print("\nDatabase query failed!")
        sys.exit(1) 