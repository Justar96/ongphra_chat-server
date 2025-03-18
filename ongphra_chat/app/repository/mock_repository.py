from typing import List, Dict, Any, Optional, TypeVar, Generic, Type
from pydantic import BaseModel
import logging

from app.repository.base import BaseRepository
from app.core.logging import get_logger
from app.domain.meaning import Category, CategoryCombination, Reading

class MockCategoryRepository:
    """Mock repository for categories"""
    
    def __init__(self):
        """Initialize the mock category repository"""
        self.logger = logging.getLogger("MockCategoryRepository")
        self.logger.info("Initialized MockCategoryRepository")
        
        # Create some mock categories
        self.categories = [
            Category(
                id=1,
                name="RELATIONSHIP",
                thai_meaning="ความรัก",
                house_number=5,
                house_type="personal",
                description="Relationships and love"
            ),
            Category(
                id=2,
                name="FINANCE",
                thai_meaning="การเงิน",
                house_number=2,
                house_type="material",
                description="Finance and wealth"
            ),
            Category(
                id=3,
                name="CAREER",
                thai_meaning="การงาน",
                house_number=6,
                house_type="work",
                description="Career and work"
            ),
            Category(
                id=4,
                name="HEALTH",
                thai_meaning="สุขภาพ",
                house_number=6,
                house_type="physical",
                description="Health and wellness"
            ),
            Category(
                id=5,
                name="FAMILY",
                thai_meaning="ครอบครัว",
                house_number=4,
                house_type="personal",
                description="Family and home"
            )
        ]
        
        # Create some mock combinations
        self.combinations = [
            {
                "id": 1,
                "file_name": "relationship_finance",
                "category1_id": 1,
                "category2_id": 2,
                "category3_id": None
            },
            {
                "id": 2,
                "file_name": "career_health",
                "category1_id": 3,
                "category2_id": 4,
                "category3_id": None
            },
            {
                "id": 3,
                "file_name": "family_relationship",
                "category1_id": 5,
                "category2_id": 1,
                "category3_id": None
            }
        ]
    
    async def get_by_id(self, id: int) -> Optional[Category]:
        """Get category by ID"""
        self.logger.debug(f"Getting category by ID: {id}")
        for category in self.categories:
            if category.id == id:
                return category
        return None
    
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        self.logger.debug(f"Getting category by name: {name}")
        for category in self.categories:
            if category.name == name:
                return category
        return None
    
    async def get_by_thai_name(self, thai_name: str) -> Optional[Category]:
        """Get category by Thai name"""
        self.logger.debug(f"Getting category by Thai name: {thai_name}")
        for category in self.categories:
            if category.thai_meaning == thai_name:
                return category
        return None
    
    async def search_by_thai_meaning(self, keyword: str) -> List[Category]:
        """Search categories by Thai meaning containing the keyword"""
        self.logger.debug(f"Searching categories with Thai meaning containing: {keyword}")
        results = []
        for category in self.categories:
            if keyword.lower() in category.thai_meaning.lower():
                results.append(category)
        return results
    
    async def get_combination_by_id(self, combination_id: int) -> Optional[Dict[str, Any]]:
        """Get category combination by ID"""
        self.logger.debug(f"Getting combination by ID: {combination_id}")
        for combination in self.combinations:
            if combination["id"] == combination_id:
                return combination
        return None


class MockReadingRepository:
    """Mock repository for readings"""
    
    def __init__(self):
        """Initialize the mock reading repository"""
        self.logger = logging.getLogger("MockReadingRepository")
        self.logger.info("Initialized MockReadingRepository")
        
        # Create some mock readings
        self.readings = [
            Reading(
                id=1,
                combination_id=1,
                heading="ความรักและการเงิน",
                meaning="คุณจะพบกับความรักที่มั่นคงและมีฐานะทางการเงินที่ดี",
                influence_type="positive",
                file_name="relationship_finance"
            ),
            Reading(
                id=2,
                combination_id=2,
                heading="อาชีพและสุขภาพ",
                meaning="การงานของคุณจะก้าวหน้า แต่ต้องระวังเรื่องสุขภาพ",
                influence_type="neutral",
                file_name="career_health"
            ),
            Reading(
                id=3,
                combination_id=3,
                heading="ครอบครัวและความรัก",
                meaning="ครอบครัวของคุณจะมีความสุข และความรักจะเบ่งบาน",
                influence_type="positive",
                file_name="family_relationship"
            )
        ]
    
    async def get_by_categories(self, category_ids: List[int]) -> List[Reading]:
        """Get readings by category IDs"""
        self.logger.debug(f"Getting readings for category IDs: {category_ids}")
        if not category_ids:
            self.logger.warning("No category IDs provided for reading lookup")
            return []
        
        results = []
        for reading in self.readings:
            combination_id = reading.combination_id
            # Find the combination
            for combination in MockCategoryRepository().combinations:
                if combination["id"] == combination_id:
                    # Check if any of the categories match
                    if (combination["category1_id"] in category_ids or
                        combination["category2_id"] in category_ids or
                        (combination["category3_id"] and combination["category3_id"] in category_ids)):
                        results.append(reading)
                        break
        
        return results
    
    async def get_by_base_and_position(self, base: int, position: int) -> List[Reading]:
        """Get readings by base and position"""
        self.logger.debug(f"Getting readings for base {base}, position {position}")
        # For simplicity, just return all readings
        return self.readings 