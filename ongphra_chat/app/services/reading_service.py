# app/services/reading_service.py
from typing import Dict, List, Optional, Tuple, Any
import re
from fastapi import Depends
from datetime import datetime
from functools import lru_cache
import time

from app.domain.bases import BasesResult
from app.domain.meaning import Reading, Category, MeaningCollection, Meaning, FortuneReading
from app.repository.reading_repository import ReadingRepository
from app.repository.category_repository import CategoryRepository
from app.core.logging import get_logger
from app.core.exceptions import ReadingError
from app.services.calculator import CalculatorService
from app.services.session_service import get_session_manager
from app.services.ai_topic_service import AITopicService, UserMapping, MappingAnalysis, TopicDetectionResult
from app.core.error_handler import catch_errors


class ReadingMatcher:
    """Helper class for matching readings with calculator results"""
    
    def __init__(self, logger):
        """Initialize the reading matcher"""
        self.logger = logger
        
        # Compile regex patterns for performance
        self.element_pattern = re.compile(r'\(([^)]+)\)')
        self.position_pattern = re.compile(r'\(([^)]+)\)')
        self.value_pattern = re.compile(r'[:：]\s*(\d+)')
        self.digit_pattern = re.compile(r'\b(\d+)\b')
    
    def extract_attributes_from_heading(self, reading: Reading) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Extract base, position, and value from reading heading when database fields are missing
        
        Args:
            reading: The reading to analyze
            
        Returns:
            Tuple of (base, position, value) extracted from the heading
        """
        if not reading or not hasattr(reading, 'heading') or not reading.heading:
            return None, None, None
            
        try:
            # Initialize with None values
            extracted_base, extracted_position, extracted_value = None, None, None
            
            # First, look for Thai position names in the heading
            position_mappings = {
                # Base 1 (Day)
                'อัตตะ': (1, 1),
                'หินะ': (1, 2),
                'ธานัง': (1, 3),
                'ปิตา': (1, 4),
                'มาตา': (1, 5),
                'โภคา': (1, 6),
                'มัชฌิมา': (1, 7),
                # Base 2 (Month)
                'ตะนุ': (2, 1),
                'กดุมภะ': (2, 2),
                'สหัชชะ': (2, 3),
                'พันธุ': (2, 4),
                'ปุตตะ': (2, 5),
                'อริ': (2, 6),
                'ปัตนิ': (2, 7),
                # Base 3 (Year)
                'มรณะ': (3, 1),
                'สุภะ': (3, 2),
                'กัมมะ': (3, 3),
                'ลาภะ': (3, 4),
                'พยายะ': (3, 5),
                'ทาสา': (3, 6),
                'ทาสี': (3, 7)
            }
            
            # Base name mappings (Thai to index)
            base_name_mappings = {
                'วัน': 1,     # Day
                'เดือน': 2,   # Month
                'ปี': 3,      # Year
                'ผลรวม': 4,   # Sum
                'ฐาน1': 1,
                'ฐาน2': 2,
                'ฐาน3': 3,
                'ฐาน4': 4
            }
            
            heading = reading.heading.strip()
            
            # Extract position names from parentheses
            position_matches = self.position_pattern.findall(heading)
            
            # Process the found position names
            for position_name in position_matches:
                position_name = position_name.strip()
                if position_name in position_mappings:
                    extracted_base, extracted_position = position_mappings[position_name]
                    break
            
            # Look for base names in the heading (like "ฐาน1", "วัน", etc.)
            for base_name, base_index in base_name_mappings.items():
                if base_name in heading:
                    extracted_base = base_index
                    break
            
            # Look for values (numbers 1-9) in the heading
            # First try looking for value after colon
            value_match = self.value_pattern.search(heading)
            if value_match:
                try:
                    value = int(value_match.group(1))
                    if 1 <= value <= 9:
                        extracted_value = value
                except ValueError:
                    pass
            
            # If value not found through colon pattern, try finding any standalone digit
            if extracted_value is None:
                digit_matches = self.digit_pattern.findall(heading)
                for match in digit_matches:
                    try:
                        value = int(match)
                        if 1 <= value <= 9:
                            extracted_value = value
                            break
                    except ValueError:
                        continue
            
            # If still no value found, try to extract from content
            if extracted_value is None and hasattr(reading, 'content'):
                content = reading.content
                if content:
                    # Look for numbers in first line of content
                    first_line = content.split('\n')[0]
                    digit_matches = re.findall(r'\b(\d+)\b', first_line)
                    for match in digit_matches:
                        try:
                            value = int(match)
                            if 1 <= value <= 9:
                                extracted_value = value
                                break
                        except ValueError:
                            continue
            
            # If we have a base but no position, try to infer position from value
            if extracted_base is not None and extracted_position is None and extracted_value is not None:
                # Each base has 7 positions, try to map value to position
                if 1 <= extracted_value <= 7:
                    extracted_position = extracted_value
            
            # If we have a position but no base, default to base 1
            if extracted_base is None and extracted_position is not None:
                extracted_base = 1
            
            # If we have neither base nor position but have a value, use defaults
            if extracted_base is None and extracted_position is None and extracted_value is not None:
                extracted_base = 1
                extracted_position = 1
            
            self.logger.debug(f"Extracted from heading '{heading[:30]}...': Base={extracted_base}, Position={extracted_position}, Value={extracted_value}")
            return extracted_base, extracted_position, extracted_value
            
        except Exception as e:
            self.logger.error(f"Error extracting attributes from heading: {str(e)}")
            return None, None, None
    
    def matches_calculator_result(self, reading: Reading, calculator_result: BasesResult) -> bool:
        """
        Check if a reading matches the values in the calculator result
        
        Args:
            reading: The reading to check
            calculator_result: The calculator result with bases
            
        Returns:
            True if the reading matches, False otherwise
        """
        try:
            # Get base and position, either from reading attributes or from heading
            base = getattr(reading, 'base', None)
            position = getattr(reading, 'position', None)
            reading_value = getattr(reading, 'value', None)
            
            # If any attributes are missing, try to extract them from the heading
            if base is None or position is None or reading_value is None:
                extracted_base, extracted_position, extracted_value = self.extract_attributes_from_heading(reading)
                
                # Use extracted values if available
                if base is None and extracted_base is not None:
                    base = extracted_base
                if position is None and extracted_position is not None:
                    position = extracted_position
                if reading_value is None and extracted_value is not None:
                    reading_value = extracted_value
            
            # Log the reading attributes for debugging
            self.logger.debug(f"Checking reading - Base: {base}, Position: {position}, Value: {reading_value}")
            
            # If still missing essential attributes, can't match
            if base is None and position is None:
                self.logger.debug(f"Reading missing both base and position: {reading.heading[:50]}")
                return True  # Allow matching to continue with defaults
                
            # Get the base sequence if we have a base
            if base is not None:
                if not 1 <= base <= 4:
                    self.logger.debug(f"Invalid base: {base}")
                    return False
                    
                base_sequences = {
                    1: calculator_result.bases.base1,
                    2: calculator_result.bases.base2, 
                    3: calculator_result.bases.base3,
                    4: calculator_result.bases.base4
                }
                
                sequence = base_sequences.get(base, [])
                
                # Check if position is within sequence bounds
                if position is not None:
                    if not 1 <= position <= 7:
                        self.logger.debug(f"Invalid position: {position}")
                        return False
                        
                    if position > len(sequence):
                        self.logger.debug(f"Position {position} out of bounds for base {base} (length: {len(sequence)})")
                        return False
                        
                    # Get the value at this position
                    actual_value = sequence[position - 1]  # Convert to 0-indexed
                    
                    # If reading specifies a value, it must match (with some flexibility)
                    if reading_value is not None:
                        # Try modulo 9 matching (common in some numerology systems)
                        mod9_match = (reading_value % 9 == actual_value % 9) and reading_value > 0 and actual_value > 0
                        
                        if mod9_match:
                            self.logger.debug(f"Value mod9 match: {reading_value} ≈ {actual_value}")
                            return True
                        elif reading_value == actual_value:
                            self.logger.debug(f"Direct value match: {reading_value} == {actual_value}")
                            return True
                        else:
                            self.logger.debug(f"Value mismatch: {reading_value} != {actual_value}")
                            return False
                    
                    # If no value specified in reading, consider it a match
                    return True
            
            # If we have no base but have a position, try matching against all bases
            if base is None and position is not None:
                for b in range(1, 5):
                    sequence = getattr(calculator_result.bases, f"base{b}", [])
                    if position <= len(sequence):
                        actual_value = sequence[position - 1]
                        if reading_value is None or reading_value == actual_value:
                            self.logger.debug(f"Found match in base {b} at position {position}")
                            return True
            
            # If we only have a value, check if it appears in any base
            if base is None and position is None and reading_value is not None:
                for b in range(1, 5):
                    sequence = getattr(calculator_result.bases, f"base{b}", [])
                    if reading_value in sequence:
                        self.logger.debug(f"Found value {reading_value} in base {b}")
                        return True
            
            # If we have no specific attributes to match, consider it a potential match
            if base is None and position is None and reading_value is None:
                return True
                
            return False
                
        except Exception as e:
            self.logger.error(f"Error matching calculator result: {str(e)}")
            return False

    def calculate_match_score(self, base: int, position: int, value: Optional[int] = None) -> float:
        """
        Calculate a match score based on base, position, and value
        
        Args:
            base: The base number (1-4)
            position: The position number (1-7)
            value: The value at this position (optional)
            
        Returns:
            A match score between 0 and 1
        """
        # Base weights - some bases are considered more significant than others
        base_weights = {
            1: 0.95,  # Day base (highest significance)
            2: 0.90,  # Month base (high significance)
            3: 0.85,  # Year base (medium significance)
            4: 0.80   # Sum base (lowest significance)
        }
        
        # Position weights - some positions are more significant than others
        position_weights = {
            1: 1.0,    # First position (highest significance)
            2: 0.95,   # Second position
            3: 0.90,   # Third position
            4: 0.85,   # Fourth position
            5: 0.80,   # Fifth position
            6: 0.75,   # Sixth position
            7: 0.70    # Seventh position (lowest significance)
        }
        
        # Get base and position weights, default to 0.7 if invalid
        base_weight = base_weights.get(base, 0.7)
        position_weight = position_weights.get(position, 0.7)
        
        # Calculate combined score
        score = base_weight * position_weight
        
        # Adjust for value if provided
        if value is not None and value > 0 and value <= 9:
            # Values with special significance (e.g., 1, 9) could get bonus
            value_bonus = {
                1: 0.05,  # Beginning of the sequence
                9: 0.05   # End of the sequence
            }
            score += value_bonus.get(value, 0)
        
        # Ensure score doesn't exceed 1.0
        return min(score, 1.0)


class ReadingService:
    """Service for extracting and matching readings from calculator results"""
    
    def __init__(
        self,
        reading_repository: ReadingRepository,
        category_repository: CategoryRepository
    ):
        """Initialize ReadingService"""
        self.reading_repository = reading_repository
        self.category_repository = category_repository
        self.logger = get_logger(__name__)
        
        # Initialize AI topic service
        from app.services.ai_topic_service import get_ai_topic_service
        self.ai_topic_service = get_ai_topic_service()
        
        # Initialize labels for positions
        self.day_labels = ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
        self.month_labels = ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"]
        self.year_labels = ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]
        
        # Cache for readings to avoid database hits
        self._reading_cache = {}
        
        self.logger.info("ReadingService initialized")
        
        # Compile regex patterns for performance
        self.element_pattern = re.compile(r'\(([^)]+)\)')
        
        # Cache for category lookups
        self._category_cache = {}
        
        # Cache for meanings
        self._meanings_cache = {}
        
        self.calculator_service = CalculatorService()
        
        self.matcher = ReadingMatcher(self.logger)
    
    async def extract_elements_from_heading(self, heading: str) -> Tuple[str, str]:
        """
        Extract element names from a reading heading
        
        Example: "สินทรัพย์ (โภคา) สัมพันธ์กับ เพื่อนฝูง การติดต่อ (สหัชชะ)"
        Returns: ("โภคา", "สหัชชะ")
        """
        self.logger.debug(f"Extracting elements from heading: {heading}")
        
        if not heading:
            return ("", "")
            
        # Extract elements in parentheses using compiled regex
        elements = self.element_pattern.findall(heading)
        
        if len(elements) < 2:
            self.logger.warning(f"Could not extract two elements from heading: {heading}")
            return ("", "")
        
        # Return the first two elements found
        return (elements[0], elements[1])
    
    async def get_category_by_element_name(self, element_name: str) -> Optional[Category]:
        """Get category by element name, with caching"""
        if not element_name:
            return None
            
        # Check cache first
        if element_name in self._category_cache:
            return self._category_cache[element_name]
            
        self.logger.debug(f"Looking up category for element name: {element_name}")
        
        # First try to find by category_name
        category = await self.category_repository.get_by_name(element_name)
        
        # If not found, try by thai_name
        if not category:
            self.logger.debug(f"Category not found by name, trying Thai name: {element_name}")
            category = await self.category_repository.get_by_thai_name(element_name)
        
        if not category:
            self.logger.warning(f"No category found for element name: {element_name}")
        else:
            self.logger.debug(f"Found category: {category.id} - {category.category_name}")
            # Add to cache
            self._category_cache[element_name] = category
            
        return category
    
    async def get_readings_for_base_position(self, base: int, position: int) -> List[Reading]:
        """
        Get readings for a specific base and position
        
        Args:
            base: Base number (1-4)
            position: Position number (1-7)
            
        Returns:
            List of readings that match the base and position
        """
        self.logger.debug(f"Getting readings for base {base}, position {position}")
        
        # Define Thai position names for each base
        thai_positions = {
            1: ['อัตตะ', 'หินะ', 'ธานัง', 'ปิตา', 'มาตา', 'โภคา', 'มัชฌิมา'],  # Base 1 (Day)
            2: ['ตะนุ', 'กดุมภะ', 'สหัชชะ', 'พันธุ', 'ปุตตะ', 'อริ', 'ปัตนิ'],  # Base 2 (Month)
            3: ['มรณะ', 'สุภะ', 'กัมมะ', 'ลาภะ', 'พยายะ', 'ทาสา', 'ทาสี'],    # Base 3 (Year)
        }
        
        try:
            # Get the Thai position name if available
            thai_position_name = ""
            if base < 4 and position <= len(thai_positions[base]):
                thai_position_name = thai_positions[base][position - 1]  # Convert to 0-indexed for array access
                self.logger.debug(f"Base {base}, Position {position} corresponds to '{thai_position_name}'")
            
            # Try to get readings in two ways:
            
            # 1. First, try to get by house_number
            readings = await self.reading_repository.get_by_base_and_position(base, position)
            
            # 2. If no readings found and we have a Thai position name, try by category name
            if not readings and thai_position_name:
                # Get the category for this Thai position
                category = await self.get_category_by_element_name(thai_position_name)
                if category:
                    self.logger.debug(f"Found category {category.id} for '{thai_position_name}', querying readings by category")
                    readings = await self.reading_repository.get_by_categories([category.id])
            
            self.logger.debug(f"Found {len(readings)} readings for base {base}, position {position}")
            return readings
        except Exception as e:
            self.logger.error(f"Error getting readings for base {base}, position {position}: {str(e)}")
            raise ReadingError(f"Failed to get readings: {str(e)}")
    
    def _log_calculator_result_details(self, calculator_result: BasesResult) -> None:
        """
        Log detailed information about calculator result for debugging
        
        Args:
            calculator_result: The calculator result to analyze
        """
        try:
            self.logger.info("Calculator Result Details:")
            
            # Log birth info with safe attribute access
            birth_info = getattr(calculator_result, 'birth_info', None)
            if not birth_info:
                self.logger.warning("No birth_info found in calculator result")
                return
            
            # Safe attribute access
            birth_date_str = "Unknown"
            if hasattr(birth_info, 'date') and birth_info.date:
                try:
                    birth_date_str = birth_info.date.strftime('%Y-%m-%d')
                except Exception:
                    birth_date_str = str(birth_info.date)
                    
            day = getattr(birth_info, 'day', "Unknown")
            day_value = getattr(birth_info, 'day_value', 0)
            year_animal = getattr(birth_info, 'year_animal', "Unknown")
            year_start_number = getattr(birth_info, 'year_start_number', 0)
            
            self.logger.info(f"Birth Info: {birth_date_str}, {day} (value: {day_value})")
            self.logger.info(f"Year animal: {year_animal}, Year start: {year_start_number}")
            
            # Check if bases attribute exists
            if not hasattr(calculator_result, 'bases'):
                self.logger.warning("No bases found in calculator result")
                return
                
            # Log bases with safe access
            bases = calculator_result.bases
            base1 = getattr(bases, 'base1', [])
            base2 = getattr(bases, 'base2', [])
            base3 = getattr(bases, 'base3', [])
            base4 = getattr(bases, 'base4', [])
            
            self.logger.info(f"Base 1 (Day): {base1}")
            self.logger.info(f"Base 2 (Month): {base2}")
            self.logger.info(f"Base 3 (Year): {base3}")
            self.logger.info(f"Base 4 (Sum): {base4}")
            
            # Log expected positions for key matches
            base_labels = {
                1: ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"],
                2: ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"],
                3: ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]
            }
            
            # Log each position's value
            for base_num in range(1, 5):
                base_key = f"base{base_num}"
                base_values = getattr(bases, base_key, [])
                
                if base_num < 4 and base_values:
                    labels = base_labels[base_num]
                    for i, (label, value) in enumerate(zip(labels, base_values)):
                        self.logger.info(f"Base {base_num}, Position {i+1} ({label}): {value}")
                elif base_values:
                    for i, value in enumerate(base_values):
                        self.logger.info(f"Base 4, Position {i+1}: {value}")
        except Exception as e:
            self.logger.error(f"Error logging calculator result details: {str(e)}", exc_info=True)

    async def _find_readings_by_categories(
        self, 
        calculator_result: BasesResult,
        base_num: int,
        position: int
    ) -> List[Meaning]:
        """
        Find readings based on category names mapped from base and position
        This method aligns with the database schema where readings are linked to category combinations
        
        Args:
            calculator_result: The calculator result
            base_num: Base number (1-4)
            position: Position in the base (1-7)
            
        Returns:
            List of matching meanings
        """
        try:
            # Define Thai position names for each base
            thai_positions = {
                1: ['อัตตะ', 'หินะ', 'ธานัง', 'ปิตา', 'มาตา', 'โภคา', 'มัชฌิมา'],  # Base 1 (Day)
                2: ['ตะนุ', 'กดุมภะ', 'สหัชชะ', 'พันธุ', 'ปุตตะ', 'อริ', 'ปัตนิ'],  # Base 2 (Month)
                3: ['มรณะ', 'สุภะ', 'กัมมะ', 'ลาภะ', 'พยายะ', 'ทาสา', 'ทาสี'],    # Base 3 (Year)
            }
            
            # Skip if invalid base or position
            if base_num not in thai_positions or position > len(thai_positions[base_num]):
                return []
                
            # Get category name for this base and position
            category_name = thai_positions[base_num][position - 1]  # Convert to 0-indexed
            
            # Get value from calculator result
            base_sequence = getattr(calculator_result.bases, f"base{base_num}", [])
            value = base_sequence[position - 1] if position <= len(base_sequence) else 0
            
            self.logger.debug(f"Finding readings for Base {base_num}, Position {position}, Category {category_name}, Value {value}")
            
            # Try to get category from repository
            category = await self.category_repository.get_by_name(category_name)
            if not category:
                self.logger.warning(f"Category not found: {category_name}")
                return []
                
            # Get readings for this category
            readings = await self.reading_repository.get_by_categories([category.id])
            
            # Convert to meanings
            meanings = []
            for reading in readings:
                meaning = Meaning(
                    id=getattr(reading, 'id', None),
                    base=base_num,
                    position=position,
                    value=value,
                    heading=getattr(reading, 'heading', ''),
                    content=getattr(reading, 'content', ''),
                    category=category_name,
                    match_score=0.9  # High score for category-based matches
                )
                meanings.append(meaning)
                
            self.logger.debug(f"Found {len(meanings)} readings for category {category_name}")
            return meanings
            
        except Exception as e:
            self.logger.error(f"Error finding readings by category: {str(e)}")
            return []

    def _log_match_statistics(self, direct_matches: int, category_matches: int, flexible_matches: int, total_unique: int) -> None:
        """
        Log detailed statistics about the matching process
        
        Args:
            direct_matches: Number of direct matches found
            category_matches: Number of category matches found
            flexible_matches: Number of flexible matches found
            total_unique: Total number of unique meanings after deduplication
        """
        self.logger.info("===== MATCH STATISTICS =====")
        self.logger.info(f"Direct matches: {direct_matches}")
        self.logger.info(f"Category matches: {category_matches}")
        self.logger.info(f"Flexible matches: {flexible_matches}")
        self.logger.info(f"Total matches before deduplication: {direct_matches + category_matches + flexible_matches}")
        self.logger.info(f"Total unique matches: {total_unique}")
        self.logger.info("============================")
        
    def _extract_attributes_from_heading(self, reading: Reading) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        return self.matcher.extract_attributes_from_heading(reading)

    def _matches_calculator_result(self, reading: Reading, calculator_result: BasesResult) -> bool:
        return self.matcher.matches_calculator_result(reading, calculator_result)

    def _calculate_match_score(self, base: int, position: int, value: Optional[int] = None) -> float:
        return self.matcher.calculate_match_score(base, position, value)

    async def extract_meanings_from_calculator_result(self, calculator_result: BasesResult) -> List[Meaning]:
        """
        Extract meanings from calculator result using a progressive matching approach
        
        This method tries several matching strategies in order:
        1. Direct matching based on base, position, and value
        2. Category-based matching 
        3. Flexible matching as a fallback
        
        Args:
            calculator_result: The calculator result with bases
            
        Returns:
            List of meanings extracted from the readings
        """
        try:
            # Start timer for performance logging
            import time
            start_time = time.time()
            
            # Verify that calculator_result has required attributes
            if not hasattr(calculator_result, 'bases') or not hasattr(calculator_result, 'birth_info'):
                self.logger.error("Invalid calculator result: missing required attributes")
                return []
                
            # Log calculator result details for debugging
            self._log_calculator_result_details(calculator_result)
            
            # Generate cache key
            try:
                hash_key = self._generate_hash_key(calculator_result)
                cache_key = f"meanings:{hash_key}"
                
                # Check cache if available
                # We'll use in-memory class cache
                if hash_key in self._meanings_cache:
                    self.logger.info(f"Found cached meanings for calculator result")
                    return self._meanings_cache[hash_key]
            except Exception as cache_error:
                self.logger.error(f"Error with cache operations: {str(cache_error)}")
                # Continue without caching if there's an error
            
            # Step 1: Get all readings once to avoid multiple database queries
            self.logger.info("Fetching all readings from database")
            all_readings = await self.reading_repository.get_all()
            self.logger.info(f"Fetched {len(all_readings)} total readings from database")
            
            # Progressive matching approach:
            
            # 1. First try direct matching with base, position, and value
            self.logger.info("Attempting direct matching with calculator result")
            direct_matches = []
            for reading in all_readings:
                # A reading matches if base, position, and value align with calculator result
                if self._matches_calculator_result(reading, calculator_result):
                    # Extract base and position from reading or heading
                    base, position, value = self._extract_attributes_from_heading(reading)
                    
                    # If we couldn't extract from heading, try direct attributes
                    if base is None:
                        base = getattr(reading, 'base', 1)  # Default to base 1 if not found
                    if position is None:
                        position = getattr(reading, 'position', 1)  # Default to position 1 if not found
                    if value is None:
                        value = getattr(reading, 'value', 1)  # Default to value 1 if not found
                    
                    # Calculate match score
                    match_score = self._calculate_match_score(base, position, value)
                    
                    # Get the meaning content, trying different attribute names
                    meaning_content = getattr(reading, 'meaning', None)
                    if not meaning_content:
                        meaning_content = getattr(reading, 'content', None)
                    if not meaning_content:
                        meaning_content = getattr(reading, 'thai_content', "ไม่พบเนื้อหาการทำนาย")
                    
                    # Create meaning with all required fields
                    meaning = Meaning(
                        id=getattr(reading, 'id', None),
                        base=base,
                        position=position,
                        value=value,
                        heading=getattr(reading, 'heading', 'คำทำนาย'),
                        meaning=meaning_content,
                        category=getattr(reading, 'category', 'ทั่วไป'),
                        match_score=match_score
                    )
                    direct_matches.append(meaning)
            
            self.logger.info(f"Found {len(direct_matches)} direct matches from calculator result")
            
            # 2. Try category-based matching if not enough direct matches
            category_matches = []
            if len(direct_matches) < 10:  # Increased threshold for better results
                self.logger.info("Direct matches insufficient, trying category-based matching")
                
                # Try finding matches for all positions in all bases
                for base_num in range(1, 5):  # Bases 1-4
                    for position in range(1, 8):  # Positions 1-7
                        # Don't query for positions beyond the actual length of the base
                        base_sequence = getattr(calculator_result.bases, f"base{base_num}", [])
                        if base_num <= 3 and position <= len(base_sequence):
                            found_matches = await self._find_readings_by_categories(calculator_result, base_num, position)
                            if found_matches:
                                self.logger.debug(f"Found {len(found_matches)} category matches for Base {base_num}, Position {position}")
                                category_matches.extend(found_matches)
                
                self.logger.info(f"Found {len(category_matches)} total category-based matches")
            
            # Step 3: If still not enough matches, try more flexible matching
            flexible_matches = []
            if len(direct_matches) + len(category_matches) < 3:
                self.logger.info("Still not enough matches, trying flexible matching")
                # Implementation of more flexible matching strategies could go here
                # For example, matching on influence_type or related categories
            
            # Log match statistics
            self._log_match_statistics(
                len(direct_matches), 
                len(category_matches), 
                len(flexible_matches),
                len(direct_matches) + len(category_matches) + len(flexible_matches)
            )
            
            # Combine all matches, removing duplicates based on ID
            all_meanings = direct_matches + category_matches + flexible_matches
            
            # Remove duplicates, keeping the one with the highest match score
            seen_headings = {}
            unique_meanings = []
            
            for meaning in all_meanings:
                heading = getattr(meaning, 'heading', '')
                if heading in seen_headings:
                    existing_index = seen_headings[heading]
                    # Keep the meaning with the higher match score
                    if getattr(meaning, 'match_score', 0) > getattr(unique_meanings[existing_index], 'match_score', 0):
                        unique_meanings[existing_index] = meaning
                else:
                    seen_headings[heading] = len(unique_meanings)
                    unique_meanings.append(meaning)
            
            # Sort by match score, highest first
            result = sorted(unique_meanings, key=lambda m: getattr(m, 'match_score', 0), reverse=True)
            
            # Limit results to a reasonable number
            result = result[:50]  # Return top 50 meanings
            
            # Cache the results in memory
            try:
                self._meanings_cache[hash_key] = result
                # Limit the cache size to prevent memory issues
                if len(self._meanings_cache) > 100:
                    # Remove oldest entry (not the most efficient but works for now)
                    oldest_key = next(iter(self._meanings_cache))
                    self._meanings_cache.pop(oldest_key)
            except Exception as cache_error:
                self.logger.error(f"Error caching results: {str(cache_error)}")
            
            # Log processing time
            elapsed_time = time.time() - start_time
            self.logger.info(f"Meaning extraction completed in {elapsed_time:.2f} seconds with {len(result)} meanings")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting meanings from calculator result: {str(e)}", exc_info=True)
            return []

    def _generate_hash_key(self, calculator_result: BasesResult) -> str:
        """Generate a hash key for caching based on calculator result"""
        import hashlib
        import json
        
        try:
            # Safe access to bases data
            bases = getattr(calculator_result, 'bases', None)
            birth_info = getattr(calculator_result, 'birth_info', None)
            
            if not bases or not birth_info:
                self.logger.warning("Missing bases or birth_info in calculator result")
                # Generate a simpler hash with timestamp as fallback
                timestamp = str(int(time.time()))
                return hashlib.md5(timestamp.encode()).hexdigest()
            
            # Safe attribute access for date
            birth_date_str = None
            if hasattr(birth_info, 'date') and birth_info.date:
                try:
                    birth_date_str = birth_info.date.isoformat()
                except Exception:
                    # If date can't be converted to ISO format, use string representation
                    birth_date_str = str(birth_info.date)
            
            # Extract the essential parts of the calculator result with safe attribute access
            bases_data = {
                "base1": getattr(bases, 'base1', []),
                "base2": getattr(bases, 'base2', []),
                "base3": getattr(bases, 'base3', []),
                "base4": getattr(bases, 'base4', []),
                "date": birth_date_str,
                "day": getattr(birth_info, 'day', None),
                "day_value": getattr(birth_info, 'day_value', 0),
                "month": getattr(birth_info, 'month', 0),
                "year_animal": getattr(birth_info, 'year_animal', None),
                "year_start_number": getattr(birth_info, 'year_start_number', 0)
            }
            
            # Convert to JSON and hash
            data_str = json.dumps(bases_data, sort_keys=True)
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception as e:
            self.logger.error(f"Error generating hash key: {str(e)}")
            # Fallback to a simpler hash if there's an error
            timestamp = str(int(time.time()))
            return hashlib.md5(timestamp.encode()).hexdigest()

    def _filter_and_rank_meanings(self, meanings: List[Meaning], user_question: Optional[str] = None) -> List[Meaning]:
        """Filter and rank meanings more efficiently"""
        try:
            # Start with all meanings
            filtered_meanings = meanings.copy()
            
            # If no question, return top 200 meanings by match score
            if not user_question:
                filtered_meanings.sort(key=lambda m: m.match_score, reverse=True)
                return filtered_meanings[:200]
            
            # Calculate relevance scores based on question
            for meaning in filtered_meanings:
                # Base score from initial matching
                score = meaning.match_score
                
                # Boost score based on question relevance
                if user_question:
                    # Check if question keywords appear in meaning
                    question_words = set(user_question.lower().split())
                    meaning_words = set(meaning.meaning.lower().split())
                    heading_words = set(meaning.heading.lower().split())
                    
                    # Calculate word overlap
                    meaning_overlap = len(question_words & meaning_words)
                    heading_overlap = len(question_words & heading_words)
                    
                    # Boost score based on overlap
                    score += meaning_overlap * 0.5  # Less weight for meaning overlap
                    score += heading_overlap * 1.0  # More weight for heading overlap
                
                meaning.match_score = score
            
            # Sort by final score and return top 200
            filtered_meanings.sort(key=lambda m: m.match_score, reverse=True)
            return filtered_meanings[:200]
            
        except Exception as e:
            self.logger.error(f"Error in filtering meanings: {str(e)}", exc_info=True)
            return meanings[:200]  # Return first 200 as fallback
    
    @catch_errors(
        error_message="Error getting fortune reading",
        fallback_value=None,
        reraise=False
    )
    async def get_fortune_reading(
        self,
        birth_date: Optional[datetime] = None,
        thai_day: Optional[str] = None,
        user_question: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> FortuneReading:
        """Get a fortune reading based on birth date and optional user question"""
        try:
            if not birth_date:
                return FortuneReading(
                    heading="กรุณาระบุวันเกิด",
                    meaning="ต้องการวันเกิดเพื่อทำนายดวงชะตา",
                    influence_type="ทั่วไป",
                    birth_date="",
                    thai_day=""
                )

            # Calculate bases using calculator service
            try:
                calculator_result = self.calculator_service.calculate_birth_bases(birth_date, thai_day)
                self.logger.debug(f"Calculator result generated successfully: {birth_date.strftime('%Y-%m-%d')}")
                
                # Verify that the calculator result has the expected structure
                if not hasattr(calculator_result, 'bases') or not hasattr(calculator_result, 'birth_info'):
                    raise ValueError("Invalid calculator result structure: missing required attributes")
                
                # Ensure birth_info has necessary attributes
                birth_info = calculator_result.birth_info
                if not hasattr(birth_info, 'date') or not hasattr(birth_info, 'day'):
                    raise ValueError("Invalid birth_info structure: missing required attributes")
                
            except Exception as calc_error:
                self.logger.error(f"Error calculating birth bases: {str(calc_error)}", exc_info=True)
                return FortuneReading(
                    heading="เกิดข้อผิดพลาดในการคำนวณ",
                    meaning=f"ขออภัย เกิดข้อผิดพลาดในการคำนวณ: {str(calc_error)}",
                    influence_type="ทั่วไป",
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day or ""
                )
            
            # Extract meanings from calculator result
            all_meanings = await self.extract_meanings_from_calculator_result(calculator_result)
            self.logger.info(f"Initially extracted {len(all_meanings)} meanings from calculator result")
            
            if not all_meanings:
                return FortuneReading(
                    heading="ไม่พบความหมาย",
                    meaning="ขออภัย ไม่พบความหมายที่เหมาะสม",
                    influence_type="ทั่วไป",
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day or getattr(calculator_result.birth_info, 'day', '')
                )
                
            # Filter and rank meanings for more relevant results
            meanings = self._filter_and_rank_meanings(all_meanings, user_question)
            self.logger.info(f"Filtered to {len(meanings)} relevant meanings")

            # Check if we have any meanings after filtering
            if not meanings:
                self.logger.warning("No meanings found after filtering")
                return FortuneReading(
                    heading="ขออภัย ไม่พบการทำนายที่เหมาะสม",
                    meaning="ระบบไม่พบข้อมูลการทำนายที่ตรงกับคำถามของท่าน แต่สามารถคำนวณฐานเกิดของท่านได้ดังนี้:\n" + 
                            f"วันเกิด: {birth_date.strftime('%Y-%m-%d')}\n" +
                            f"วันพื้นดวง: {thai_day or getattr(calculator_result.birth_info, 'day', '')}\n" +
                            f"นักษัตร: {self._get_year_animal(birth_date.year)}",
                    influence_type="ทั่วไป",
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day or getattr(calculator_result.birth_info, 'day', ''),
                    question=user_question
                )

            # Detect topic using AI service if there's a question
            topic_result = None
            detected_topic = "ทั่วไป"  # Default topic
            
            if user_question:
                try:
                    # Detect topic using AI service
                    topic_result = await self.ai_topic_service.detect_topic(user_question)
                    detected_topic = topic_result.primary_topic
                    self.logger.info(f"AI detected topic: {detected_topic} with confidence {topic_result.confidence}")
                    
                    # Find meaning with highest match score for detected topic
                    selected_meaning = self.find_best_meaning_for_topic(meanings, topic_result)
                    
                except Exception as e:
                    self.logger.error(f"Error in AI topic detection: {str(e)}")
                    # Fall back to highest match score
                    try:
                        selected_meaning = max(meanings, key=lambda m: getattr(m, 'match_score', 0))
                    except (ValueError, TypeError):
                        selected_meaning = meanings[0] if meanings else None
            else:
                # Without question, use highest match score
                try:
                    selected_meaning = max(meanings, key=lambda m: getattr(m, 'match_score', 0))
                except (ValueError, TypeError):
                    selected_meaning = meanings[0] if meanings else None
                
            if not selected_meaning and meanings:
                # If no meaning was selected but we have meanings, use the first one
                selected_meaning = meanings[0]
                
            # If we still don't have a selected meaning, return a default reading
            if not selected_meaning:
                self.logger.warning("No meanings available for fortune reading")
                # Create basic reading from calculator result
                return FortuneReading(
                    heading="ข้อมูลฐานเกิดของท่าน",
                    meaning=(f"ฐาน1 (วันเกิด): {getattr(calculator_result.bases, 'base1', [])}\n" +
                            f"ฐาน2 (เดือนเกิด): {getattr(calculator_result.bases, 'base2', [])}\n" +
                            f"ฐาน3 (ปีเกิด): {getattr(calculator_result.bases, 'base3', [])}\n" +
                            f"ฐาน4 (ผลรวม): {getattr(calculator_result.bases, 'base4', [])}"),
                    influence_type="ทั่วไป",
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day or getattr(calculator_result.birth_info, 'day', ''),
                    question=user_question
                )
            
            # Get base and position information for additional context
            base_names = ['วัน', 'เดือน', 'ปี', 'ผลรวม']
            position_names = {
                1: ['อัตตะ', 'หินะ', 'ธานัง', 'ปิตา', 'มาตา', 'โภคา', 'มัชฌิมา'],
                2: ['ตะนุ', 'กดุมภะ', 'สหัชชะ', 'พันธุ', 'ปุตตะ', 'อริ', 'ปัตนิ'],
                3: ['มรณะ', 'สุภะ', 'กัมมะ', 'ลาภะ', 'พยายะ', 'ทาสา', 'ทาสี']
            }
            
            base = getattr(selected_meaning, 'base', 0)
            position = getattr(selected_meaning, 'position', 0)
            
            base_name = base_names[base - 1] if 0 < base <= 4 else f"ฐาน {base}"
            position_name = ""
            if base <= 3 and 0 < position <= 7:
                position_name = position_names[base][position - 1]
            
            # For debugging - log what we selected from DB
            self.logger.info(f"Selected meaning - Base: {base_name}, Position: {position_name}, Value: {getattr(selected_meaning, 'value', None)}")
            self.logger.info(f"Selected meaning - Heading: {getattr(selected_meaning, 'heading', '')}")
            self.logger.info(f"Selected meaning - Category: {getattr(selected_meaning, 'category', '')}")
            
            # First try to generate a reading with external API
            personalized_reading = await self._generate_ai_reading(
                calculator_result=calculator_result,
                birth_date=birth_date,
                thai_day=thai_day or getattr(calculator_result.birth_info, 'day', ''),
                user_question=user_question,
                selected_meaning=selected_meaning,
                topic=detected_topic,
                topic_result=topic_result
            )
            
            # If external API generation failed, try with local enhanced reading
            if not personalized_reading:
                self.logger.info("External API reading failed, trying local enhanced reading")
                personalized_reading = self._generate_enhanced_reading(
                    birth_date=birth_date,
                    thai_day=thai_day or getattr(calculator_result.birth_info, 'day', ''),
                    user_question=user_question,
                    selected_meaning=selected_meaning,
                    topic=detected_topic,
                    topic_result=topic_result,
                    base_name=base_name,
                    position_name=position_name
                )
            
            # If both methods failed, fall back to the database reading
            if not personalized_reading:
                self.logger.info("Both reading generation methods failed, using raw database content")
                # Add context to heading if not already present
                enhanced_heading = getattr(selected_meaning, 'heading', 'คำทำนาย')
                if position_name and position_name not in enhanced_heading:
                    enhanced_heading = f"{enhanced_heading} ({position_name})"
                
                return FortuneReading(
                    heading=enhanced_heading,
                    meaning=getattr(selected_meaning, 'content', getattr(selected_meaning, 'meaning', '')),
                    influence_type=getattr(selected_meaning, 'category', 'ทั่วไป'),
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day or getattr(calculator_result.birth_info, 'day', ''),
                    question=user_question
                )
            else:
                # Return the generated personalized reading
                return personalized_reading
            
        except Exception as e:
            self.logger.error(f"Error getting fortune reading: {str(e)}", exc_info=True)
            return FortuneReading(
                heading="เกิดข้อผิดพลาด",
                meaning="ขออภัย เกิดข้อผิดพลาดในการทำนาย",
                influence_type="ทั่วไป",
                birth_date=birth_date.strftime("%Y-%m-%d") if birth_date else "",
                thai_day=thai_day or ""
            )

    async def _generate_ai_reading(
        self,
        calculator_result: BasesResult,
        birth_date: datetime,
        thai_day: str,
        user_question: Optional[str],
        selected_meaning: Meaning,
        topic: str,
        topic_result: Optional['TopicDetectionResult'] = None
    ) -> Optional[FortuneReading]:
        """
        Generate a reading using the AI service
        
        This method uses the AI service to generate a detailed reading based on the user's birth information,
        bases, user question, and a selected meaning.
        """
        try:
            # Check if required modules exist before importing
            import importlib.util
            ai_spec = importlib.util.find_spec("app.services.ai")
            prompt_spec = importlib.util.find_spec("app.services.prompt")
            
            if not ai_spec or not prompt_spec:
                missing_modules = []
                if not ai_spec:
                    missing_modules.append("app.services.ai")
                if not prompt_spec:
                    missing_modules.append("app.services.prompt")
                self.logger.warning(f"Required modules not found: {', '.join(missing_modules)}. Skipping AI reading generation.")
                return None
                
            # Safe imports after verifying modules exist
            from app.services.prompt import PromptService
            from app.services.openai_service import OpenAIService
            
            # Import here to avoid circular imports
            ai_service = OpenAIService()
            prompt_service = PromptService()
            
            # Create MeaningService if needed
            meaning_service = None
            try:
                from app.services.meaning import MeaningService
                meaning_service = MeaningService(self.category_repository, self.reading_repository)
            except ImportError:
                self.logger.warning("MeaningService module not found, proceeding with limited functionality")
            
            # Get birth info and bases from calculator result
            birth_info = calculator_result.birth_info
            bases = calculator_result.bases
            
            # Get additional meanings for context if MeaningService is available
            meaning_collection = None
            user_mappings = None
            
            if meaning_service:
                meaning_collection = await meaning_service.extract_meanings(bases, user_question or "")
                user_mappings = await meaning_service.create_user_mappings(bases)
            
            # Get topic analysis with mapping analysis
            detected_topic = None
            mapping_analysis = None
            if user_question:
                # Use class instance of ai_topic_service
                topic_detection_result = await self.ai_topic_service.detect_topic(
                    user_question, 
                    user_mappings=user_mappings
                )
                detected_topic = topic_detection_result.primary_topic
                mapping_analysis = topic_detection_result.mapping_analysis
                
                self.logger.info(f"Detected topic: {detected_topic}, Mapping analysis: {len(mapping_analysis) if mapping_analysis else 0} items")
            
            # Generate system prompt without user-specific context
            system_prompt = prompt_service.generate_system_prompt(
                language="thai",  # Default to Thai for now
                topic=detected_topic
            )
            
            # Generate user prompt with all available information
            user_prompt = prompt_service.generate_user_prompt(
                birth_info=birth_info,
                bases=bases,
                meanings=meaning_collection,
                question=user_question or "ดวงชะตาโดยทั่วไป",  # Default to general reading if no question
                language="thai",  # Default to Thai for now
                topic=detected_topic,
                mapping_analysis=mapping_analysis  # Include mapping analysis in prompt
            )
            
            # Generate the reading with the AI service
            ai_content = await ai_service.generate_content(system_prompt, user_prompt)
            
            if not ai_content:
                self.logger.error("AI service returned empty response")
                return None
                
            # Extract heading and content
            heading, content = self._split_heading_content(ai_content)
            
            # Create and return the reading
            reading = FortuneReading(
                birth_date=birth_date.strftime("%Y-%m-%d"),
                thai_day=thai_day,
                year_animal=self._get_year_animal(birth_date.year),
                question=user_question or "ดวงชะตาโดยทั่วไป",
                heading=heading,
                meaning=content,
                source="ai",
                category_id=selected_meaning.id if hasattr(selected_meaning, 'id') else None,
                meaning_id=selected_meaning.id if hasattr(selected_meaning, 'id') else None,
                topic=detected_topic or topic,
                base=selected_meaning.base,
                position=selected_meaning.position,
                value=selected_meaning.value
            )
            
            return reading
            
        except ImportError as e:
            self.logger.error(f"Missing module for AI reading generation: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error generating AI reading: {str(e)}", exc_info=True)
            return None
    
    def _get_year_animal(self, year: int) -> str:
        """Get Thai zodiac animal for a given year"""
        animals = [
            "ชวด (หนู)", "ฉลู (วัว)", "ขาล (เสือ)", "เถาะ (กระต่าย)", 
            "มะโรง (งูใหญ่)", "มะเส็ง (งูเล็ก)", "มะเมีย (ม้า)", "มะแม (แพะ)", 
            "วอก (ลิง)", "ระกา (ไก่)", "จอ (หมา)", "กุน (หมู)"
        ]
        return animals[(year - 4) % 12]
    
    def _determine_influence_type(
        self,
        meaning: str,
        topic: str,
        original_category: str
    ) -> str:
        """
        Determine the influence type based on the reading content and topic
        
        Args:
            meaning: The reading content
            topic: The detected topic
            original_category: The original category from the database
            
        Returns:
            str: The determined influence type
        """
        try:
            # First try to use the topic as influence type
            if topic in ['การเงิน', 'ความรัก', 'สุขภาพ', 'การงาน', 'การศึกษา', 'ครอบครัว', 'โชคลาภ', 'อนาคต', 'การเดินทาง']:
                return topic
                
            # If topic is not a standard influence type, analyze the content
            positive_keywords = ['ดี', 'เจริญ', 'รุ่งเรือง', 'สำเร็จ', 'โชคลาภ', 'มั่งมี', 'สมหวัง', 'สุข']
            negative_keywords = ['ไม่ดี', 'ระวัง', 'อันตราย', 'เสีย', 'ยาก', 'ลำบาก', 'ทุกข์']
            
            positive_count = sum(1 for word in positive_keywords if word in meaning)
            negative_count = sum(1 for word in negative_keywords if word in meaning)
            
            if positive_count > negative_count:
                return 'ดี'
            elif negative_count > positive_count:
                return 'ไม่ดี'
            else:
                # If counts are equal or no keywords found, use original category
                return original_category
                
        except Exception as e:
            self.logger.error(f"Error determining influence type: {str(e)}")
            return original_category
    
    def find_best_meaning_for_topic(self, meanings: List[Meaning], topic_result: Optional['TopicDetectionResult']) -> Optional[Meaning]:
        """
        Find the best meaning for a detected topic
        
        Args:
            meanings: List of meaning candidates
            topic_result: Topic detection result from AI
            
        Returns:
            The best matching meaning or None if no match
        """
        try:
            if not meanings:
                self.logger.warning("No meanings provided for topic matching")
                return None
                
            if not topic_result:
                self.logger.warning("Invalid topic result for topic matching")
                return max(meanings, key=lambda m: getattr(m, 'match_score', 0))
                
            primary_topic = topic_result.primary_topic
            self.logger.info(f"Finding best meaning for topic: {primary_topic}")
            
            # Special handling for general topics - avoid specific categories
            if primary_topic == "ทั่วไป":
                self.logger.info("General topic detected - prioritizing general readings")
                
                # List of specific categories to avoid for general readings
                specific_categories = ['การเงิน', 'ความรัก', 'สุขภาพ', 'การงาน', 
                                      'กดุมภะ', 'ลาภะ', 'โภคา', 'ธานัง', 'ปัตนิ', 'ปิตา']
                
                # First try to find truly general readings
                general_meanings = []
                for meaning in meanings:
                    category = getattr(meaning, 'category', '')
                    heading = getattr(meaning, 'heading', '')
                    
                    # Check if this meaning looks like a specialized one
                    is_specialized = any(cat.lower() in (category + ' ' + heading).lower() for cat in specific_categories)
                    
                    if not is_specialized:
                        # Higher score for truly general readings
                        meaning.match_score = getattr(meaning, 'match_score', 0) + 3.0
                        general_meanings.append(meaning)
                
                if general_meanings:
                    self.logger.info(f"Found {len(general_meanings)} general meanings")
                    # Return the highest scoring general meaning
                    return max(general_meanings, key=lambda m: getattr(m, 'match_score', 0))
                
                # If no general meanings found, continue with normal selection but deprioritize finances
                self.logger.info("No purely general meanings found, using regular scoring with adjustments")
                for meaning in meanings:
                    category = getattr(meaning, 'category', '')
                    heading = getattr(meaning, 'heading', '')
                    
                    # Reduce score for financial readings when general topic is requested
                    if any(cat in (category + ' ' + heading).lower() for cat in ['เงิน', 'ทรัพย์', 'การเงิน', 'ธุรกิจ', 'กดุมภะ', 'ลาภะ', 'โภคา']):
                        meaning.match_score = getattr(meaning, 'match_score', 0) - 2.0
                
                # Return the best match after score adjustments
                return max(meanings, key=lambda m: getattr(m, 'match_score', 0))
            
            # Define related categories for each topic to improve matching
            topic_related_categories = {
                'การเงิน': ['หินะ', 'ทรัพย์', 'เงิน', 'ธุรกิจ', 'กดุมภะ', 'ลาภะ', 'โภคา', 'ธานัง'],
                'ความรัก': ['มาตา', 'คู่ครอง', 'ความรัก', 'ปุตตะ', 'ปัตนิ', 'สหัชชะ'],
                'สุขภาพ': ['โภคา', 'อัตตะ', 'ร่างกาย', 'สุขภาพ', 'ตะนุ', 'มรณะ'],
                'การงาน': ['โภคา', 'กัมมะ', 'อาชีพ', 'หน้าที่', 'งาน', 'ทาสา', 'ทาสี'],
                'การศึกษา': ['ธานัง', 'การเรียนรู้', 'วิชาการ', 'สหัชชะ', 'ปุตตะ'],
                'ครอบครัว': ['ปิตา', 'มาตา', 'บ้าน', 'ครอบครัว', 'พันธุ', 'ปุตตะ'],
                'โชคลาภ': ['ลาภะ', 'โชค', 'หินะ', 'ทรัพย์', 'สุภะ', 'กดุมภะ'],
                'อนาคต': ['พยายะ', 'อนาคต', 'แนวโน้ม', 'ทิศทาง', 'ลาภะ'],
                'การเดินทาง': ['ธานัง', 'สหัชชะ', 'เดินทาง', 'ย้ายถิ่น', 'สุภะ']
            }
            
            # Default to general categories if topic not found
            related_categories = topic_related_categories.get(primary_topic, ['กัมมะ', 'ลาภะ', 'สุภะ', 'อัตตะ'])
            
            # Get secondary topics for broader matching
            secondary_topics = topic_result.secondary_topics
            for secondary_topic in secondary_topics:
                if secondary_topic in topic_related_categories:
                    related_categories.extend(topic_related_categories[secondary_topic])
            
            # Make the list unique
            related_categories = list(set(related_categories))
            self.logger.debug(f"Related categories for topic matching: {', '.join(related_categories)}")
            
            # Initial scoring based on category matches
            scored_meanings = []
            for meaning in meanings:
                # Start with the existing match score
                base_score = getattr(meaning, 'match_score', 5.0)
                
                # Extract category from meaning
                category = getattr(meaning, 'category', '')
                
                # Check for direct or partial category match
                category_match_score = 0.0
                for related_cat in related_categories:
                    if category and related_cat.lower() in category.lower():
                        category_match_score = 2.0
                        break
                
                # Check if this is a significant position based on base and value
                position_score = self._calculate_match_score(
                    getattr(meaning, 'base', 1),
                    getattr(meaning, 'position', 1),
                    getattr(meaning, 'value', 0)
                )
                
                # Combine scores
                final_score = base_score + category_match_score + (position_score / 5.0)
                
                # Add to candidates with final score
                scored_meanings.append((meaning, final_score))
                
            # Sort by final score (highest first)
            scored_meanings.sort(key=lambda x: x[1], reverse=True)
            
            # Log top matches for debugging
            if scored_meanings:
                num_to_log = min(3, len(scored_meanings))
                self.logger.info(f"Top {num_to_log} meaning matches for topic '{primary_topic}':")
                for i in range(num_to_log):
                    m, score = scored_meanings[i]
                    self.logger.info(f"  {i+1}. Score: {score:.1f}, Base: {getattr(m, 'base', 'N/A')}, " +
                                  f"Position: {getattr(m, 'position', 'N/A')}, " +
                                  f"Category: {getattr(m, 'category', 'N/A')}, " +
                                  f"Heading: {getattr(m, 'heading', 'N/A')[:30]}...")
            
            # Return best match or None if no matches
            return scored_meanings[0][0] if scored_meanings else None
            
        except Exception as e:
            self.logger.error(f"Error finding best meaning for topic: {str(e)}", exc_info=True)
            # Fallback to highest match score
            try:
                return max(meanings, key=lambda m: getattr(m, 'match_score', 0))
            except Exception:
                return meanings[0] if meanings else None

    def _generate_enhanced_reading(
        self,
        birth_date: datetime,
        thai_day: str,
        user_question: Optional[str],
        selected_meaning: Meaning,
        topic: str,
        topic_result: Optional['TopicDetectionResult'] = None,
        base_name: str = "",
        position_name: str = ""
    ) -> Optional[FortuneReading]:
        """
        Generate an enhanced reading without external API calls
        
        This method creates a more user-friendly reading by:
        1. Using a clear topic-specific heading
        2. Adding context about which base/position is relevant
        3. Structuring the content in readable paragraphs
        4. Adding topic-specific insights
        """
        try:
            self.logger.info(f"Generating local enhanced reading for topic: {topic}")
            
            # Generate topic-specific heading
            topic_headings = {
                'การเงิน': "คำทำนายเรื่องการเงินและทรัพย์สิน",
                'ความรัก': "คำทำนายเรื่องความรักและความสัมพันธ์",
                'สุขภาพ': "คำทำนายเรื่องสุขภาพและความเป็นอยู่",
                'การงาน': "คำทำนายเรื่องการงานและอาชีพ",
                'การศึกษา': "คำทำนายเรื่องการศึกษาและการเรียนรู้",
                'ครอบครัว': "คำทำนายเรื่องครอบครัวและบ้าน",
                'โชคลาภ': "คำทำนายเรื่องโชคลาภและความสำเร็จ",
                'อนาคต': "คำทำนายเรื่องอนาคตและชะตาชีวิต",
                'การเดินทาง': "คำทำนายเรื่องการเดินทางและการย้ายถิ่น",
                'ทั่วไป': "คำทำนายเรื่องทั่วไป"
            }
            
            # Get heading based on topic
            heading = topic_headings.get(topic, f"คำทำนายเรื่อง{topic}")
            
            # Add confidence indication to heading if available
            if topic_result and topic_result.confidence > 7:
                heading += " (แม่นยำสูง)"
                
            # Get the raw meaning content
            raw_meaning = selected_meaning.meaning
            
            # For general topic, check if the reading is overly focused on a specific area
            if topic == "ทั่วไป":
                # Financial keywords to look for
                financial_keywords = ['เงิน', 'ทอง', 'ทรัพย์', 'สมบัติ', 'ธุรกิจ', 'กำไร', 'รายได้', 'ลงทุน', 'การเงิน', 'ฐานะ']
                
                # Count financial keywords
                financial_count = sum(1 for kw in financial_keywords if kw in raw_meaning.lower())
                
                # If the reading is heavily focused on finances but the topic is general, add balance
                if financial_count >= 3 and len(raw_meaning.split()) >= 20:
                    self.logger.info("General topic with financial focus detected, adding balance")
                    
                    # Add balanced aspects of life to provide a more general reading
                    additional_context = "\n\nนอกจากด้านการเงินแล้ว คุณยังมีโอกาสดีในด้านความสัมพันธ์และการพัฒนาตนเอง " \
                        "คุณมีความสามารถในการสร้างความสัมพันธ์ที่ดีกับผู้คนรอบข้าง และมีแนวโน้มที่จะประสบความสำเร็จในสิ่งที่ตั้งใจทำ " \
                        "ควรให้ความสำคัญกับการดูแลสุขภาพและครอบครัวควบคู่ไปกับการพัฒนาด้านการงานและการเงิน"
                    
                    # Append to the raw meaning
                    raw_meaning += additional_context
            
            # Structure the meaning into paragraphs if it's not already
            paragraphs = raw_meaning.split("\n")
            if len(paragraphs) <= 1:
                # If the meaning is just one paragraph, try to split by periods
                parts = raw_meaning.split(". ")
                if len(parts) > 1:
                    # Group parts into approximately 2-3 sentences per paragraph
                    group_size = max(1, len(parts) // 3)
                    new_paragraphs = []
                    for i in range(0, len(parts), group_size):
                        group = parts[i:i+group_size]
                        # Add period back to the end of sentences except the last part
                        for j in range(len(group) - 1):
                            group[j] += "."
                        # Last part might already have a period
                        if not group[-1].endswith("."):
                            group[-1] += "."
                        new_paragraphs.append(" ".join(group))
                    paragraphs = new_paragraphs
            
            # Create introduction paragraph
            intro = f"จากการคำนวณฐาน{base_name} ตำแหน่ง{position_name} ของคุณ ทำนายได้ว่า:\n\n"
            
            # Add contextual paragraph at the end based on the topic
            topic_context = {
                'การเงิน': "ในด้านการเงิน คุณควรระมัดระวังการใช้จ่ายและวางแผนการเงินอย่างรอบคอบในช่วงนี้ การลงทุนควรพิจารณาอย่างรอบด้านและไม่ประมาท",
                'ความรัก': "สำหรับความรัก การสื่อสารอย่างเปิดใจจะช่วยเสริมสร้างความเข้าใจและความสัมพันธ์ที่ดี ให้ความสำคัญกับความรู้สึกของคนรอบข้าง",
                'สุขภาพ': "ด้านสุขภาพ ควรดูแลตัวเองอย่างสม่ำเสมอ ออกกำลังกายพอประมาณและพักผ่อนให้เพียงพอ หลีกเลี่ยงความเครียดสะสม",
                'การงาน': "ในเรื่องการงาน ความขยันและความอดทนจะนำไปสู่ความสำเร็จ อย่ากลัวที่จะเรียนรู้สิ่งใหม่ๆและพัฒนาทักษะของตัวเอง",
                'การศึกษา': "สำหรับการศึกษา ควรตั้งใจเรียนและแบ่งเวลาอย่างมีประสิทธิภาพ การทบทวนบทเรียนอย่างสม่ำเสมอจะช่วยให้เข้าใจเนื้อหาได้ดียิ่งขึ้น",
                'ครอบครัว': "ในด้านครอบครัว ควรให้เวลากับคนในครอบครัวและรับฟังความคิดเห็นของทุกคน ความเข้าใจและการให้อภัยจะช่วยรักษาความสัมพันธ์ที่ดี",
                'โชคลาภ': "สำหรับโชคลาภ โอกาสดีๆ อาจเข้ามาโดยไม่คาดคิด แต่อย่าหวังพึ่งโชคชะตาเพียงอย่างเดียว ความพยายามและความขยันเป็นสิ่งสำคัญ",
                'อนาคต': "สำหรับอนาคต การวางแผนและเตรียมพร้อมรับมือกับการเปลี่ยนแปลงจะช่วยให้คุณก้าวไปข้างหน้าได้อย่างมั่นคง",
                'การเดินทาง': "ในเรื่องการเดินทาง ควรวางแผนและเตรียมตัวให้พร้อม ศึกษาข้อมูลเส้นทางและสถานที่ให้ละเอียดเพื่อความปลอดภัยและความราบรื่น",
                'ทั่วไป': "การสร้างสมดุลในชีวิตทั้งด้านการงาน การเงิน ความสัมพันธ์ และสุขภาพ จะนำมาซึ่งความสุขและความสำเร็จที่ยั่งยืน ใช้ชีวิตด้วยความไม่ประมาทและมีสติอยู่เสมอ"
            }
            
            conclusion = f"\n\n{topic_context.get(topic, 'ขอให้คุณพบเจอแต่สิ่งดีๆ และมีความสุขในชีวิต')}"
            
            # Build the complete meaning
            meaning = intro + "\n".join(paragraphs) + conclusion
            
            # Determine influence type
            influence_type = self._determine_influence_type(meaning, topic, selected_meaning.category)
            
            self.logger.info(f"Successfully generated enhanced local reading for topic: {topic}")
            
            return FortuneReading(
                heading=heading,
                meaning=meaning,
                influence_type=influence_type,
                birth_date=birth_date.strftime("%Y-%m-%d"),
                thai_day=thai_day,
                question=user_question
            )
        except Exception as e:
            self.logger.error(f"Error generating enhanced reading: {str(e)}", exc_info=True)
            return None

    def _split_heading_content(self, ai_content: str) -> Tuple[str, str]:
        """
        Split AI-generated content into heading and content parts
        
        Args:
            ai_content: The full content generated by AI
            
        Returns:
            A tuple of (heading, content)
        """
        if not ai_content:
            return ("คำทำนาย", "")
            
        # Try to find markdown heading or pattern with newlines
        lines = ai_content.strip().split('\n')
        
        # Check for markdown heading
        if lines[0].startswith('# '):
            heading = lines[0].replace('# ', '')
            content = '\n'.join(lines[1:]).strip()
            return (heading, content)
            
        # Check for heading with asterisks
        if lines[0].startswith('**') and lines[0].endswith('**'):
            heading = lines[0].replace('**', '')
            content = '\n'.join(lines[1:]).strip()
            return (heading, content)
            
        # Check if first line is short (likely a heading)
        if len(lines) > 1 and len(lines[0]) < 100 and lines[0].endswith(':'):
            heading = lines[0].rstrip(':')
            content = '\n'.join(lines[1:]).strip()
            return (heading, content)
            
        # If we can't detect a proper heading, generate one
        if len(lines) > 1:
            # Use first line as heading if it's reasonably short
            if len(lines[0]) < 100:
                heading = lines[0]
                content = '\n'.join(lines[1:]).strip()
                return (heading, content)
                
        # Default - use a generic heading
        heading = "คำทำนายดวงชะตา"
        return (heading, ai_content)


# Factory function for dependency injection
async def get_reading_service(
    reading_repository: ReadingRepository = Depends(),
    category_repository: CategoryRepository = Depends()
) -> ReadingService:
    """Get reading service instance when called from code or through dependency injection"""
    # For direct calls outside of FastAPI's dependency injection system,
    # we need to create new repository instances
    try:
        # If this is called directly (not through FastAPI's DI system)
        # Just create new repositories directly
        from app.repository.reading_repository import get_reading_repository
        from app.repository.category_repository import get_category_repository
        
        # Always create new repositories when called directly
        direct_reading_repo = get_reading_repository()
        direct_category_repo = get_category_repository()
        
        return ReadingService(direct_reading_repo, direct_category_repo)
    except Exception as e:
        # Log the error but don't crash
        import logging
        logging.error(f"Error in get_reading_service: {str(e)}")
        
        # Create repositories directly as a last resort
        from app.domain.meaning import Reading, Category
        from app.repository.reading_repository import ReadingRepository
        from app.repository.category_repository import CategoryRepository
        
        reading_repo = ReadingRepository(Reading)
        category_repo = CategoryRepository(Category)
        
        return ReadingService(reading_repo, category_repo)