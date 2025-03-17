# app/repository/category_repository.py
from typing import List, Optional, Dict, Any

from ongphra_chat.app.repository.db_repository import DBRepository
from ongphra_chat.app.domain.meaning import Category
from ongphra_chat.app.core.logging import get_logger


class CategoryRepository(DBRepository[Category]):
    """Repository for categories"""
    
    def __init__(self, model_class=Category):
        """Initialize the category repository"""
        super().__init__(model_class, "categories")
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initialized CategoryRepository")
    
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        self.logger.debug(f"Getting category by name: {name}")
        try:
            query = "SELECT * FROM categories WHERE name = %s"
            result = await self.execute_raw_query(query, name)
            if result and len(result) > 0:
                return self.model_class(**result[0])
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving category by name {name}: {str(e)}", exc_info=True)
            raise
    
    async def get_by_thai_name(self, thai_name: str) -> Optional[Category]:
        """Get category by Thai meaning/name"""
        self.logger.debug(f"Getting category by Thai name: {thai_name}")
        try:
            query = "SELECT * FROM categories WHERE thai_meaning = %s"
            result = await self.execute_raw_query(query, thai_name)
            if result and len(result) > 0:
                return self.model_class(**result[0])
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving category by Thai name {thai_name}: {str(e)}", exc_info=True)
            raise
    
    async def get_by_house_number(self, house_number: int) -> List[Category]:
        """Get categories by house number"""
        self.logger.debug(f"Getting categories for house number: {house_number}")
        try:
            query = "SELECT * FROM categories WHERE house_number = %s ORDER BY name"
            results = await self.execute_raw_query(query, house_number)
            categories = [self.model_class(**row) for row in results]
            self.logger.debug(f"Found {len(categories)} categories for house number {house_number}")
            return categories
        except Exception as e:
            self.logger.error(f"Error retrieving categories for house number {house_number}: {str(e)}", exc_info=True)
            raise
    
    async def get_by_house_type(self, house_type: str) -> List[Category]:
        """Get categories by house type"""
        self.logger.debug(f"Getting categories for house type: {house_type}")
        try:
            query = "SELECT * FROM categories WHERE house_type = %s ORDER BY house_number, name"
            results = await self.execute_raw_query(query, house_type)
            categories = [self.model_class(**row) for row in results]
            self.logger.debug(f"Found {len(categories)} categories for house type {house_type}")
            return categories
        except Exception as e:
            self.logger.error(f"Error retrieving categories for house type {house_type}: {str(e)}", exc_info=True)
            raise
    
    async def get_category_combinations(self) -> List[Dict[str, Any]]:
        """Get all category combinations with their related categories"""
        self.logger.debug("Getting all category combinations")
        try:
            query = """
                SELECT cc.id, cc.file_name, 
                    c1.id AS category1_id, c1.name AS category1_name, 
                    c2.id AS category2_id, c2.name AS category2_name,
                    c3.id AS category3_id, c3.name AS category3_name
                FROM category_combinations cc
                JOIN categories c1 ON cc.category1_id = c1.id
                JOIN categories c2 ON cc.category2_id = c2.id
                LEFT JOIN categories c3 ON cc.category3_id = c3.id
                ORDER BY cc.file_name
            """
            results = await self.execute_raw_query(query)
            self.logger.debug(f"Found {len(results)} category combinations")
            return results
        except Exception as e:
            self.logger.error(f"Error retrieving category combinations: {str(e)}", exc_info=True)
            raise
    
    async def get_combination_by_categories(self, category1_id: int, category2_id: int, category3_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get category combination by category IDs"""
        self.logger.debug(f"Getting combination for categories: {category1_id}, {category2_id}, {category3_id}")
        try:
            if category3_id:
                query = """
                    SELECT * FROM category_combinations 
                    WHERE category1_id = %s AND category2_id = %s AND category3_id = %s
                """
                results = await self.execute_raw_query(query, category1_id, category2_id, category3_id)
            else:
                query = """
                    SELECT * FROM category_combinations 
                    WHERE category1_id = %s AND category2_id = %s AND category3_id IS NULL
                """
                results = await self.execute_raw_query(query, category1_id, category2_id)
            
            if results and len(results) > 0:
                return results[0]
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving combination for categories {category1_id}, {category2_id}, {category3_id}: {str(e)}", exc_info=True)
            raise