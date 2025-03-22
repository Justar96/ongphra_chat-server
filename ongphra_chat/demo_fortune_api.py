import requests
import json
from datetime import datetime

def format_json(data):
    """Format JSON data with indentation for readability."""
    return json.dumps(data, indent=2, ensure_ascii=False)

def calculate_fortune(birthdate, detail_level="normal"):
    """Calculate fortune using the API."""
    url = "http://localhost:8000/fortune/calculate"
    
    params = {
        "birthdate": birthdate,
        "detail_level": detail_level
    }
    
    try:
        # Make the API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

def main():
    """Main function to demonstrate fortune calculation."""
    print("Fortune Calculation API Demo")
    print("===========================")
    
    # Get birthdate input
    birthdate_input = input("Enter birthdate (DD-MM-YYYY) or leave empty for default (14-02-1996): ")
    birthdate = birthdate_input if birthdate_input else "14-02-1996"
    
    # Get detail level input
    print("\nDetail Levels:")
    print("  simple - Basic fortune summary")
    print("  normal - Standard fortune details")
    print("  detailed - Comprehensive fortune analysis")
    detail_level_input = input("Enter detail level (simple/normal/detailed) or leave empty for normal: ")
    detail_level = detail_level_input if detail_level_input else "normal"
    
    print(f"\nCalculating fortune for birthdate: {birthdate}, detail level: {detail_level}...")
    
    # Call the API
    result = calculate_fortune(birthdate, detail_level)
    
    if result:
        print("\nFortune Calculation Result:")
        print("=========================")
        print(f"Birthdate: {result['birthdate']}")
        print(f"Day of Week: {result['day_of_week']}")
        print(f"Zodiac Year: {result['zodiac_year']}")
        print("\nBase Values:")
        for base, value in result['base_values'].items():
            print(f"  {base}: {value}")
        
        print("\nTop Categories:")
        for base, category in result['top_categories'].items():
            print(f"  {base}: {category['thai_name']} ({category['meaning']}) - Value: {category['value']}")
        
        print("\nTop Pairs:")
        for pair in result['top_pairs']:
            print(f"\n{pair['rank']}. {pair['heading']}")
            print(f"   {pair['categories']}")
            print(f"   {pair['meaning']}")
            print(f"   Influence: {pair['influence']}")
        
        print("\nSummary:")
        print(result['summary'])
    else:
        print("Failed to calculate fortune. Please check the API server is running.")

if __name__ == "__main__":
    main() 