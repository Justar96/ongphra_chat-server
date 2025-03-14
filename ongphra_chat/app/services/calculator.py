# app/services/calculator.py
from datetime import datetime
from typing import Dict, List, Tuple

from app.domain.birth import BirthInfo
from app.domain.bases import Bases, BasesResult
from app.core.exceptions import CalculationError


class CalculatorService:
    """Service for calculating birth bases"""
    
    def __init__(self):
        # Thai zodiac years mapping
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
    
    def get_zodiac_animal(self, birth_year: int) -> str:
        """Get the zodiac animal for a given year"""
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
        
        return zodiac_map[year_mod]
    
    def calculate_base1(self, thai_day: str) -> List[int]:
        """Calculate Base 1 sequence from Thai day"""
        if thai_day not in self.day_values:
            raise CalculationError(f"Invalid Thai day: {thai_day}")
        
        return self.day_values[thai_day]["sequence"]
    
    def calculate_base2(self, month: int) -> List[int]:
        """Calculate Base 2 sequence from month"""
        if month not in self.month_sequences:
            raise CalculationError(f"Invalid month: {month}")
        
        return self.month_sequences[month]
    
    def calculate_base3(self, birth_year: int) -> Tuple[List[int], str]:
        """Calculate Base 3 sequence from birth year"""
        # Get zodiac animal
        zodiac_animal = self.get_zodiac_animal(birth_year)
        
        # Get start number from zodiac
        start_number = self.zodiac_years[zodiac_animal]
        
        # Generate sequence based on start number
        current = start_number
        sequence = []
        
        for _ in range(7):
            sequence.append(current)
            current = current % 7 + 1
            
        return sequence, zodiac_animal
    
    def calculate_base4(self, base1: List[int], base2: List[int], base3: List[int]) -> List[int]:
        """Calculate Base 4 sequence by summing bases 1-3"""
        base4 = []
        for position in range(7):
            # Sum of this position from bases 1-3
            position_sum = (
                base1[position] + 
                base2[position] + 
                base3[position]
            )
            base4.append(position_sum)
        return base4
    
    def calculate_birth_bases(self, birth_date: datetime, thai_day: str) -> BasesResult:
        """Calculate all bases for birth date and Thai day"""
        try:
            # Calculate Base 1
            base1 = self.calculate_base1(thai_day)
            
            # Calculate Base 2
            base2 = self.calculate_base2(birth_date.month)
            
            # Calculate Base 3
            base3, zodiac_animal = self.calculate_base3(birth_date.year)
            
            # Calculate Base 4
            base4 = self.calculate_base4(base1, base2, base3)
            
            # Create BirthInfo
            birth_info = BirthInfo(
                date=birth_date,
                day=thai_day,
                day_value=self.day_values[thai_day]["value"],
                month=birth_date.month,
                year_animal=zodiac_animal,
                year_start_number=self.zodiac_years[zodiac_animal]
            )
            
            # Create Bases
            bases = Bases(
                base1=base1,
                base2=base2,
                base3=base3,
                base4=base4
            )
            
            # Return combined result
            return BasesResult(
                birth_info=birth_info,
                bases=bases
            )
            
        except Exception as e:
            raise CalculationError(f"Error calculating birth bases: {str(e)}")