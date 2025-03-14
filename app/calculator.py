from calendar import c
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
from sklearn import base

class ThaiBirthCalculator:
    def __init__(self):
        # Thai zodiac years
        self.zodiac_years = {
            "ชวด": 1,  # Rat
            "ฉลู": 2,  # Ox
            "ขาล": 3,  # Tiger
            "เถาะ": 4,  # Rabbit
            "มะโรง": 5,  # Dragon
            "มะเส็ง": 6,  # Snake
            "มะเมีย": 7,  # Horse
            "มะแม": 8,  # Goat
            "วอก": 9,  # Monkey
            "ระกา": 10,  # Rooster
            "จอ": 11,  # Dog
            "กุน": 12,  # Pig
        }

        # Day values and sequences
        self.day_values = {
            "อาทิตย์": {"value": 1, "sequence": [1, 2, 3, 4, 5, 6, 7]},  # Sunday
            "จันทร์": {"value": 2, "sequence": [2, 3, 4, 5, 6, 7, 1]},  # Monday
            "อังคาร": {"value": 3, "sequence": [3, 4, 5, 6, 7, 1, 2]},  # Tuesday
            "พุธ": {"value": 4, "sequence": [4, 5, 6, 7, 1, 2, 3]},  # Wednesday
            "พฤหัสบดี": {"value": 5, "sequence": [5, 6, 7, 1, 2, 3, 4]},  # Thursday
            "ศุกร์": {"value": 6, "sequence": [6, 7, 1, 2, 3, 4, 5]},  # Friday
            "เสาร์": {"value": 7, "sequence": [7, 1, 2, 3, 4, 5, 6]},  # Saturday
        }

        # Month sequences
        self.month_sequences = {
            1: [1, 2, 3, 4, 5, 6, 7],   # January
            2: [2, 3, 4, 5, 6, 7, 1],   # February
            3: [3, 4, 5, 6, 7, 1, 2],   # March
            4: [4, 5, 6, 7, 1, 2, 3],   # April
            5: [5, 6, 7, 1, 2, 3, 4],   # May
            6: [6, 7, 1, 2, 3, 4, 5],   # June
            7: [7, 1, 2, 3, 4, 5, 6],   # July
            8: [1, 2, 3, 4, 5, 6, 7],   # August
            9: [2, 3, 4, 5, 6, 7, 1],   # September
            10: [3, 4, 5, 6, 7, 1, 2],  # October
            11: [4, 5, 6, 7, 1, 2, 3],  # November
            12: [5, 6, 7, 1, 2, 3, 4]   # December
        }

        # Special meanings for Base 4
        self.base4_meanings = {
            7: "ภาคินี",
            10: "ลาภี",
            11: "ราชาโชค",
            12: "ราชู",
            13: "มหาจร",
            15: "จันทร์",
            16: "โลกบาลก",
        }

    def analyze_bases(self, results: Dict) -> Dict:
        """Analyze relationships between bases"""
        analysis = {"matching_numbers": [], "column_sums": [], "patterns": []}

        bases = results["bases"]
        for position in range(7):
            numbers = [
                bases["base1"][position],
                bases["base2"][position],
                bases["base3"][position],
            ]

            # Find matching numbers
            if len(set(numbers)) < len(numbers):
                analysis["matching_numbers"].append(
                    {"position": position + 1, "numbers": numbers}
                )

            # Calculate column sums
            analysis["column_sums"].append(
                {"position": position + 1, "sum": sum(numbers), "numbers": numbers}
            )

        return analysis
    
    
    def calculate_base3_sequence(self, birth_year: int) -> List[int]:
        """
        Calculate Base 3 sequence based on zodiac year
        1. Convert to Buddhist Era and get zodiac animal
        2. Get start number from zodiac_years
        3. Generate sequence starting from that number
        """
        # Convert to Buddhist Era and get zodiac year
        buddhist_year = birth_year + 543
        year_mod = buddhist_year % 12
        
        # Map year mod to zodiac animal
        zodiac_map = {
            0: 'ขาล',    # Tiger
            1: 'เถาะ',   # Rabbit
            2: 'มะโรง',  # Dragon
            3: 'มะเส็ง', # Snake
            4: 'มะเมีย', # Horse
            5: 'มะแม',   # Goat
            6: 'วอก',    # Monkey
            7: 'ระกา',   # Rooster
            8: 'จอ',     # Dog
            9: 'กุน',    # Pig
            10: 'ชวด',   # Rat
            11: 'ฉลู'    # Ox
        }
        
        zodiac_animal = zodiac_map[year_mod]
        start_number = self.zodiac_years[zodiac_animal]
        
        # Generate sequence starting from the zodiac year's number
        sequence = []
        current = (start_number - 1) % 7
        
        for _ in range(7):
            sequence.append(current)
            current = current % 7 + 1
            
        return sequence, zodiac_animal
    
    def calculate_base4_sequence(self, bases: Dict[str, List[int]]) -> List[int]:
        """
        Calculate Base 4 sequence by summing corresponding positions from bases 1-3
        """
        base4 = []
        for position in range(7):
            # Sum of this position from bases 1-3
            position_sum = (
                bases['base1'][position] + 
                bases['base2'][position] + 
                bases['base3'][position]
            )
            base4.append(position_sum)
        return base4

    def calculate_birth_bases(self, birth_date: datetime, thai_day: str) -> Dict:
        """Calculate all bases for birth date"""
        if thai_day not in self.day_values:
            raise ValueError(f"Invalid Thai day: {thai_day}")

        base1 = self.day_values[thai_day]["sequence"]
        base2 = self.month_sequences[birth_date.month]
        
        # Calculate Base 3 with zodiac information
        base3_sequence, zodiac_animal = self.calculate_base3_sequence(birth_date.year)
        base4 = self.calculate_base4_sequence({
            "base1": base1,
            "base2": base2,
            "base3": base3_sequence,
        })

        return {
            "birth_info": {
                "date": birth_date.strftime("%Y-%m-%d"),
                "day": thai_day,
                "day_value": self.day_values[thai_day]["value"],
                "month": birth_date.month,
                "year_animal": zodiac_animal,
                "year_start_number": self.zodiac_years[zodiac_animal]
            },
            "bases": {
                "base1": base1,
                "base2": base2,
                "base3": base3_sequence,
                "base4": base4,
            },
        }

    def print_results(self, results: Dict, analysis: Dict):
        """Print formatted results"""
        print("\n=== Thai Birth Chart Analysis ===")
        print(f"\nBirth Information:")
        print(f"Date: {results['birth_info']['date']}")
        print(f"Day: {results['birth_info']['day']} (value: {results['birth_info']['day_value']})")
        print(f"Zodiac Year: {results['birth_info']['year_animal']}")
        print(f"Year Start Number: {results['birth_info']['year_start_number']}")

        print("\nBase Sequences:")
        print("\nPosition:", end="")
        for i in range(7):
            print(f"{i+1:4}", end="")
        print("\n" + "-" * 35)

        base_names = {
            "base1": "ฐาน 1",
            "base2": "ฐาน 2",
            "base3": "ฐาน 3",
            "base4": "ฐาน 4",
        }

        for base_name, sequence in results["bases"].items():
            print(f"{base_names[base_name]}: ", end="")
            for num in sequence:
                print(f"{num:4}", end="")
            print()

            # Print meanings for base4
            if base_name == "base4":
                print("Meaning: ", end="")
                for num in sequence:
                    meaning = self.base4_meanings.get(num, "")[:4]
                    print(f"{meaning:4},", end="")
                print()
                print()
                print("Analysis:Done")
                print("-----------------------------------")

def main():
    calculator = ThaiBirthCalculator()

    # Example: January 1, 1987 (Thursday)
    birth_date = datetime(2532, 5, 17)
    thai_day = "จันทร์"

    try:
        results = calculator.calculate_birth_bases(birth_date, thai_day)
        analysis = calculator.analyze_bases(results)
        calculator.print_results(results, analysis)
    except Exception as e:
        print(f"Error calculating birth chart: {str(e)}")

if __name__ == "__main__":
    main()
