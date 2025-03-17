# app/repository/category_combination_repository.py
from typing import List, Optional, Dict, Any

from app.repository.db_repository import DBRepository
from app.domain.meaning import CategoryCombination
from app.core.logging import get_logger


class CategoryCombinationRepository(DBRepository[CategoryCombination]):
    """Repository for category combinations"""
    
    def __init__(self, model_class=CategoryCombination):
        """Initialize the category combination repository"""
        super().__init__(model_class, "category_combinations")
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initialized CategoryCombinationRepository")
    
    async def get_by_categories(self, category1_id: int, category2_id: int, category3_id: Optional[int] = None) -> Optional[CategoryCombination]:
        """Get combination by category IDs"""
        self.logger.debug(f"Getting combination for categories: {category1_id}, {category2_id}, {category3_id}")
        
        try:
            if category3_id:
                query = """
                    SELECT * FROM category_combinations 
                    WHERE category1_id = $1 AND category2_id = $2 AND category3_id = $3
                    LIMIT 1
                """
                results = await self.execute_raw_query(query, category1_id, category2_id, category3_id)
            else:
                query = """
                    SELECT * FROM category_combinations 
                    WHERE category1_id = $1 AND category2_id = $2 AND category3_id IS NULL
                    LIMIT 1
                """
                results = await self.execute_raw_query(query, category1_id, category2_id)
            
            if not results:
                self.logger.debug(f"No combination found for categories: {category1_id}, {category2_id}, {category3_id}")
                return None
            
            combination = self.model_class(**results[0])
            self.logger.debug(f"Found combination: {combination.id} - {combination.file_name}")
            return combination
        except Exception as e:
            self.logger.error(f"Error retrieving combination for categories {category1_id}, {category2_id}, {category3_id}: {str(e)}", exc_info=True)
            raise
    
    async def get_all_with_details(self) -> List[Dict[str, Any]]:
        """Get all combinations with category details"""
        self.logger.debug("Getting all combinations with details")
        
        try:
            query = """
                SELECT cc.id, cc.file_name, 
                       c1.name AS category1_name, c1.thai_meaning AS category1_thai, 
                       c2.name AS category2_name, c2.thai_meaning AS category2_thai,
                       c3.name AS category3_name, c3.thai_meaning AS category3_thai
                FROM category_combinations cc
                JOIN categories c1 ON cc.category1_id = c1.id
                JOIN categories c2 ON cc.category2_id = c2.id
                LEFT JOIN categories c3 ON cc.category3_id = c3.id
                ORDER BY cc.file_name
            """
            
            results = await self.execute_raw_query(query)
            self.logger.debug(f"Found {len(results)} combination details")
            return results
        except Exception as e:
            self.logger.error(f"Error retrieving combination details: {str(e)}", exc_info=True)
            raise