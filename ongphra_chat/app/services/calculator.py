# app/services/calculator.py
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

from app.domain.birth import BirthInfo
from app.domain.bases import Bases, BasesResult
from app.core.exceptions import CalculationError
from app.core.logging import get_logger

class CalculatorService:
    """Service for calculating birth bases using the seven-nine method"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.logger.info("Initializing CalculatorService")
        
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

        # Day values mapping
        self.day_values = {
            "อาทิตย์": 1,  # Sunday
            "จันทร์": 2,  # Monday
            "อังคาร": 3,  # Tuesday
            "พุธ": 4,  # Wednesday
            "พฤหัสบดี": 5,  # Thursday
            "ศุกร์": 6,  # Friday
            "เสาร์": 7,  # Saturday
        }
        
        # Base labels for formatting output
        self.day_labels = ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
        self.month_labels = ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"]
        self.year_labels = ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]
        
        # Cache for common calculations
        self._zodiac_cache = {}
    
    def get_zodiac_animal(self, birth_year: int) -> str:
        """Get the zodiac animal for a given year with caching"""
        # Check cache first
        if birth_year in self._zodiac_cache:
            return self._zodiac_cache[birth_year]
            
        # Calculate Thai zodiac year index
        thai_zodiac_year_index = self.get_thai_zodiac_year_index(birth_year)
        
        # Map index to zodiac animal
        zodiac_map = {
            1: 'ชวด',    # Rat
            2: 'ฉลู',     # Ox
            3: 'ขาล',     # Tiger
            4: 'เถาะ',    # Rabbit
            5: 'มะโรง',   # Dragon
            6: 'มะเส็ง',  # Snake
            7: 'มะเมีย',  # Horse
            8: 'มะแม',    # Goat
            9: 'วอก',     # Monkey
            10: 'ระกา',   # Rooster
            11: 'จอ',     # Dog
            12: 'กุน'     # Pig
        }
        
        result = zodiac_map[thai_zodiac_year_index]
        # Store in cache
        self._zodiac_cache[birth_year] = result
        
        return result
    
    def get_thai_zodiac_year_index(self, year: int) -> int:
        """Determine the Thai zodiac year index based on the Gregorian year"""
        return (year - 4) % 12 + 1
    
    def generate_day_values(self, starting_value: int, total_values: int = 7) -> List[int]:
        """Generate the sequence starting from the given value"""
        values = list(range(1, total_values + 1))
        starting_index = starting_value - 1
        return values[starting_index:] + values[:starting_index]
    
    def get_day_of_week_index(self, date: datetime) -> int:
        """Get the day of the week with Sunday as 1"""
        return (date.weekday() + 1) % 7 + 1
    
    def get_wrapped_index(self, index: int, total_values: int) -> int:
        """Wrap the index to ensure it cycles within the total number of values"""
        return ((index - 1) % total_values) + 1
    
    def calculate_sum_base(self, base_1: List[int], base_2: List[int], base_3: List[int]) -> List[int]:
        """Calculate the sum of values from bases 1, 2, and 3 without wrapping"""
        return [(base_1[i] + base_2[i] + base_3[i]) for i in range(len(base_1))]
    
    def calculate_base1(self, thai_day: str) -> List[int]:
        """Calculate Base 1 sequence from Thai day"""
        if thai_day not in self.day_values:
            self.logger.error(f"Invalid Thai day: {thai_day}")
            raise CalculationError(f"Invalid Thai day: {thai_day}. Valid values are: {', '.join(self.day_values.keys())}")
        
        day_index = self.day_values[thai_day]
        self.logger.debug(f"Calculating Base 1 for day: {thai_day} (index: {day_index})")
        return self.generate_day_values(day_index)
    
    def calculate_base2(self, month: int) -> List[int]:
        """Calculate Base 2 sequence from month"""
        if month < 1 or month > 12:
            self.logger.error(f"Invalid month: {month}")
            raise CalculationError(f"Invalid month: {month}. Valid values are 1-12.")
        
        # Month with December as the first month, plus 1
        wrapped_month_index = self.get_wrapped_index(month + 1, 12)
        self.logger.debug(f"Calculating Base 2 for month: {month} (wrapped index: {wrapped_month_index})")
        return self.generate_day_values(wrapped_month_index)
    
    def calculate_base3(self, birth_year: int) -> Tuple[List[int], str]:
        """Calculate Base 3 sequence from birth year"""
        try:
            # Get Thai zodiac year index
            thai_zodiac_year_index = self.get_thai_zodiac_year_index(birth_year)
            wrapped_zodiac_year_index = self.get_wrapped_index(thai_zodiac_year_index, 12)
            
            # Get zodiac animal
            zodiac_animal = self.get_zodiac_animal(birth_year)
            
            # Generate sequence based on wrapped index
            sequence = self.generate_day_values(wrapped_zodiac_year_index)
            
            self.logger.debug(f"Calculated Base 3 for year {birth_year} (zodiac: {zodiac_animal}, index: {thai_zodiac_year_index}): {sequence}")
            return sequence, zodiac_animal
        except Exception as e:
            self.logger.error(f"Error calculating Base 3: {str(e)}")
            raise CalculationError(f"Error calculating Base 3: {str(e)}")
    
    def calculate_base4(self, base1: List[int], base2: List[int], base3: List[int]) -> List[int]:
        """Calculate Base 4 sequence by summing bases 1-3"""
        if len(base1) != 7 or len(base2) != 7 or len(base3) != 7:
            raise CalculationError("All bases must have exactly 7 elements")
            
        base4 = self.calculate_sum_base(base1, base2, base3)
        self.logger.debug(f"Calculated Base 4: {base4}")
        return base4
    
    def format_output(self, base1: List[int], base2: List[int], base3: List[int], base4: List[int]) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int], List[int]]:
        """Format the output with Thai labels for each position"""
        base1_dict = {label: value for label, value in zip(self.day_labels, base1)}
        base2_dict = {label: value for label, value in zip(self.month_labels, base2)}
        base3_dict = {label: value for label, value in zip(self.year_labels, base3)}
        
        return base1_dict, base2_dict, base3_dict, base4
    
    def validate_inputs(self, birth_date: datetime, thai_day: str) -> None:
        """Validate input parameters"""
        # Check if birth_date is valid
        if not birth_date:
            raise CalculationError("Birth date is required")
            
        # Check if thai_day is valid
        if not thai_day or thai_day not in self.day_values:
            valid_days = ", ".join(self.day_values.keys())
            raise CalculationError(f"Invalid Thai day: '{thai_day}'. Valid values are: {valid_days}")
            
        # Check if month is valid
        month = birth_date.month
        if month < 1 or month > 12:
            raise CalculationError(f"Invalid month: {month}. Month must be between 1 and 12.")
    
    def calculate_birth_bases(self, birth_date: datetime, thai_day: str) -> BasesResult:
        """Calculate all bases for birth date and Thai day"""
        try:
            self.logger.info(f"Calculating birth bases for: {birth_date.strftime('%Y-%m-%d')}, {thai_day}")
            
            # Validate inputs
            self.validate_inputs(birth_date, thai_day)
            
            # Calculate Base 1 (Day of the week)
            base1 = self.calculate_base1(thai_day)
            
            # Calculate Base 2 (Month)
            base2 = self.calculate_base2(birth_date.month)
            
            # Calculate Base 3 (Thai zodiac year)
            base3, zodiac_animal = self.calculate_base3(birth_date.year)
            
            # Calculate Base 4 (Sum of bases 1-3)
            base4 = self.calculate_base4(base1, base2, base3)
            
            # Format output with Thai labels
            base1_dict, base2_dict, base3_dict, base4_list = self.format_output(base1, base2, base3, base4)
            
            # For debugging
            self.logger.debug(f"ฐาน 1: {base1_dict}")
            self.logger.debug(f"ฐาน 2: {base2_dict}")
            self.logger.debug(f"ฐาน 3: {base3_dict}")
            self.logger.debug(f"ฐาน 4: {base4_list}")
            
            # Create BirthInfo
            birth_info = BirthInfo(
                date=birth_date,
                day=thai_day,
                day_value=self.day_values[thai_day],
                month=birth_date.month,
                year_animal=zodiac_animal,
                year_start_number=self.get_thai_zodiac_year_index(birth_date.year)
            )
            
            # Create Bases
            bases = Bases(
                base1=base1,
                base2=base2,
                base3=base3,
                base4=base4
            )
            
            # Return combined result
            self.logger.info(f"Successfully calculated bases for {birth_date.strftime('%Y-%m-%d')}")
            return BasesResult(
                birth_info=birth_info,
                bases=bases
            )
            
        except CalculationError as ce:
            self.logger.error(f"Calculation error: {str(ce)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error calculating birth bases: {str(e)}", exc_info=True)
            raise CalculationError(f"Error calculating birth bases: {str(e)}")