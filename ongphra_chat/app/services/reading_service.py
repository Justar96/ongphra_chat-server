# app/services/reading_service.py
from typing import Dict, List, Optional, Tuple
import re
from fastapi import Depends

from app.domain.bases import BasesResult
from app.domain.meaning import Reading, Category, MeaningCollection, Meaning
from app.repository.reading_repository import ReadingRepository
from app.repository.category_repository import CategoryRepository
from app.core.logging import get_logger
from app.core.exceptions import ReadingError


class ReadingService:
    """Service for extracting and matching readings from calculator results"""
    
    def __init__(
        self,
        reading_repository: ReadingRepository,
        category_repository: CategoryRepository
    ):
        """Initialize the reading service with repositories"""
        self.reading_repository = reading_repository
        self.category_repository = category_repository
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Initialized ReadingService")
    
    async def extract_elements_from_heading(self, heading: str) -> Tuple[str, str]:
        """
        Extract element names from a reading heading
        
        Example: "สินทรัพย์ (โภคา) สัมพันธ์กับ เพื่อนฝูง การติดต่อ (สหัชชะ)"
        Returns: ("โภคา", "สหัชชะ")
        """
        self.logger.debug(f"Extracting elements from heading: {heading}")
        
        # Extract elements in parentheses using regex
        elements = re.findall(r'\(([^)]+)\)', heading)
        
        if len(elements) < 2:
            self.logger.warning(f"Could not extract two elements from heading: {heading}")
            return ("", "")
        
        # Return the first two elements found
        return (elements[0], elements[1])
    
    async def get_category_by_element_name(self, element_name: str) -> Optional[Category]:
        """Get category by element name"""
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
            
        return category
    
    async def get_readings_for_base_position(self, base: int, position: int) -> List[Reading]:
        """Get readings for a specific base and position"""
        self.logger.debug(f"Getting readings for base {base}, position {position}")
        
        try:
            readings = await self.reading_repository.get_by_base_and_position(base, position)
            self.logger.debug(f"Found {len(readings)} readings for base {base}, position {position}")
            return readings
        except Exception as e:
            self.logger.error(f"Error getting readings for base {base}, position {position}: {str(e)}")
            raise ReadingError(f"Failed to get readings: {str(e)}")
    
    async def extract_meanings_from_calculator_result(
        self, 
        bases_result: BasesResult
    ) -> MeaningCollection:
        """
        Extract meanings from calculator result by matching base values with readings
        and extracting element names from headings
        """
        self.logger.info("Extracting meanings from calculator result")
        
        meanings = []
        
        # Process each base (1-4)
        for base_num in range(1, 5):
            base_values = getattr(bases_result.bases, f"base{base_num}")
            
            # Process each position (0-6)
            for position in range(7):
                value = base_values[position]
                position_num = position + 1  # Convert to 1-indexed for database
                
                # Get readings for this base and position
                readings = await self.get_readings_for_base_position(base_num, position_num)
                
                for reading in readings:
                    # Extract element names from heading
                    element1, element2 = await self.extract_elements_from_heading(reading.heading)
                    
                    # Get categories for the elements
                    category1 = await self.get_category_by_element_name(element1)
                    category2 = await self.get_category_by_element_name(element2)
                    
                    # Create category string
                    category_str = ""
                    if category1 and category2:
                        category_str = f"{category1.category_name} - {category2.category_name}"
                    
                    # Create meaning object
                    meaning = Meaning(
                        base=base_num,
                        position=position_num,
                        value=value,
                        heading=reading.heading,
                        meaning=reading.content,
                        category=category_str
                    )
                    
                    meanings.append(meaning)
        
        self.logger.info(f"Extracted {len(meanings)} meanings from calculator result")
        return MeaningCollection(items=meanings)


# Factory function for dependency injection
async def get_reading_service(
    reading_repository: ReadingRepository = Depends(),
    category_repository: CategoryRepository = Depends()
) -> ReadingService:
    """Get reading service instance"""
    return ReadingService(reading_repository, category_repository) 