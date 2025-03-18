#!/usr/bin/env python
# test_calculator_simple.py
"""
Simple test script to verify the calculator functionality
"""
import os
import sys
import json
from datetime import datetime

# Adjust Python path to find app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    # Import calculator
    from app.services.calculator import CalculatorService
    
    # Create calculator
    calculator = CalculatorService()
    
    # Test data
    birth_date = datetime(1990, 5, 15)  # May 15, 1990
    thai_day = "อังคาร"  # Tuesday
    
    print(f"Testing calculator with birth_date={birth_date}, thai_day={thai_day}")
    
    # Calculate bases
    result = calculator.calculate_birth_bases(birth_date, thai_day)
    
    print("\n=== Birth Info ===")
    print(f"Day: {result.birth_info.day}")
    print(f"Day Value: {result.birth_info.day_value}")
    print(f"Month: {result.birth_info.month}")
    print(f"Year Animal: {result.birth_info.year_animal}")
    
    print("\n=== Bases ===")
    print(f"Base 1: {result.bases.base1}")
    print(f"Base 2: {result.bases.base2}")
    print(f"Base 3: {result.bases.base3}")
    print(f"Base 4: {result.bases.base4}")
    
    # Thai position names
    day_labels = calculator.day_labels
    month_labels = calculator.month_labels
    year_labels = calculator.year_labels
    
    print("\n=== Position Labels ===")
    print(f"Day Labels: {day_labels}")
    print(f"Month Labels: {month_labels}")
    print(f"Year Labels: {year_labels}")
    
    # Print base 1 with positions
    print("\n=== Base 1 with Positions ===")
    for i, value in enumerate(result.bases.base1):
        position_name = day_labels[i] if i < len(day_labels) else f"Position {i+1}"
        print(f"{position_name}: {value}")
    
    # Print base 2 with positions
    print("\n=== Base 2 with Positions ===")
    for i, value in enumerate(result.bases.base2):
        position_name = month_labels[i] if i < len(month_labels) else f"Position {i+1}"
        print(f"{position_name}: {value}")
    
    # Print base 3 with positions
    print("\n=== Base 3 with Positions ===")
    for i, value in enumerate(result.bases.base3):
        position_name = year_labels[i] if i < len(year_labels) else f"Position {i+1}"
        print(f"{position_name}: {value}")
        
    print("\nCalculator test completed successfully!")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 