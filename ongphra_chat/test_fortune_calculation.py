import json
import datetime
from app.utils.fortune_tool import calculate_fortune

def test_fortune_calculation():
    """Test the fortune calculation with database integration."""
    birthdate = "1996-02-14"  # Example birthdate (Valentine's Day 1996)
    
    try:
        # Calculate fortune
        result = calculate_fortune(birthdate)
        
        # Print formatted birthdate and basic info
        print(f"Birthdate: {result['formatted_birthdate']}")
        print(f"Day of Week: {result['day_of_week']}")
        print(f"Zodiac Year: {result['zodiac_year']}")
        print()
        
        # Print base values
        print("Base Values:")
        print(f"Base 1: {result['bases']['base1']}")
        print(f"Base 2: {result['bases']['base2']}")
        print(f"Base 3: {result['bases']['base3']}")
        print()
        
        # Print top categories for each base
        print("Top Categories:")
        for base, category in result['top_categories'].items():
            print(f"{base}: {category['thai_name']} ({category['meaning']}) - Value: {category['value']}")
        print()
        
        # Print top 3 pairs
        print("Top Pairs:")
        for i, pair in enumerate(result['pairs'][:3]):
            print(f"{i+1}. {pair['heading']}")
            print(f"   {pair['thai_name_a']} ({pair['value_a']}) + {pair['thai_name_b']} ({pair['value_b']})")
            print(f"   {pair['meaning']}")
            print(f"   Influence: {pair['influence']}")
            print()
        
        # Print summary
        print("Summary:")
        print(result['summary'])
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_fortune_calculation() 