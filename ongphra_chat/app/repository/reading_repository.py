# app/repository/reading_repository.py
from typing import List, Optional, Dict, Any
import logging
import sys

from app.repository.db_repository import DBRepository
from app.domain.meaning import Reading
from app.core.logging import get_logger


class ReadingRepository(DBRepository[Reading]):
    """Repository for readings"""
    
    def __init__(self, model_class=Reading):
        """Initialize the reading repository"""
        super().__init__(model_class, "readings")
        
        # Add additional error handling for logger initialization
        try:
            self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
            self.logger.info(f"Initialized ReadingRepository")
        except Exception as e:
            # Fallback to basic console logging if file logging fails
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
            if not self.logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
            self.logger.warning(f"Failed to initialize file logger: {str(e)}. Using console logger instead.")
            self.logger.info(f"Initialized ReadingRepository")
    
    async def get_by_base_and_position(self, base: int, position: int) -> List[Reading]:
        """Get readings by base and position"""
        self.logger.debug(f"Getting readings for base {base}, position {position}")
        try:
            # Join with category_combinations to find the right readings
            # The base corresponds to house_number in the first category
            # The position corresponds to house_number in the second category
            query = """
                SELECT r.*, cc.file_name 
                FROM readings r
                JOIN category_combinations cc ON r.combination_id = cc.id
                JOIN categories c1 ON cc.category1_id = c1.id
                JOIN categories c2 ON cc.category2_id = c2.id
                WHERE c1.house_number = %s AND c2.house_number = %s
                ORDER BY r.id
            """
            results = await self.execute_raw_query(query, base, position)
            readings = [self.model_class(**row) for row in results]
            self.logger.debug(f"Found {len(readings)} readings for base {base}, position {position}")
            return readings
        except Exception as e:
            self.logger.error(f"Error retrieving readings for base {base}, position {position}: {str(e)}", exc_info=True)
            raise
    
    async def get_by_categories(self, category_ids: List[int]) -> List[Reading]:
        """Get readings by category IDs"""
        if not category_ids:
            self.logger.warning("No category IDs provided for reading lookup")
            return []
        
        # Create placeholders for the IN clause
        placeholders = ", ".join(["%s"] * len(category_ids))
        self.logger.debug(f"Getting readings for category IDs: {category_ids}")
        
        try:
            # Query looks for readings where any of the categories match
            query = f"""
                SELECT r.* 
                FROM readings r
                JOIN category_combinations cc ON r.combination_id = cc.id
                WHERE cc.category1_id IN ({placeholders})
                   OR cc.category2_id IN ({placeholders})
                   OR cc.category3_id IN ({placeholders})
                ORDER BY r.id
            """
            
            # Need to repeat the category_ids three times for the three IN clauses
            params = category_ids * 3  # Equivalent to category_ids + category_ids + category_ids
            
            results = await self.execute_raw_query(query, *params)
            readings = [self.model_class(**row) for row in results]
            self.logger.debug(f"Found {len(readings)} readings for category IDs: {category_ids}")
            return readings
        except Exception as e:
            self.logger.error(f"Error retrieving readings for category IDs {category_ids}: {str(e)}", exc_info=True)
            raise
    
    async def get_readings_by_combination(self, combination_id: int) -> List[Reading]:
        """Get readings by category combination ID"""
        self.logger.debug(f"Getting readings for combination ID: {combination_id}")
        try:
            query = """
                SELECT r.*, cc.file_name
                FROM readings r
                JOIN category_combinations cc ON r.combination_id = cc.id
                WHERE r.combination_id = %s
                ORDER BY r.id
            """
            results = await self.execute_raw_query(query, combination_id)
            readings = [self.model_class(**row) for row in results]
            self.logger.debug(f"Found {len(readings)} readings for combination ID {combination_id}")
            return readings
        except Exception as e:
            self.logger.error(f"Error retrieving readings for combination ID {combination_id}: {str(e)}", exc_info=True)
            raise
    
    async def get_readings_by_influence_type(self, influence_type: str) -> List[Reading]:
        """Get readings by influence type"""
        self.logger.debug(f"Getting readings for influence type: {influence_type}")
        try:
            query = """
                SELECT r.*, cc.file_name
                FROM readings r
                JOIN category_combinations cc ON r.combination_id = cc.id
                WHERE r.influence_type = %s
                ORDER BY r.id
            """
            results = await self.execute_raw_query(query, influence_type)
            readings = [self.model_class(**row) for row in results]
            self.logger.debug(f"Found {len(readings)} readings for influence type {influence_type}")
            return readings
        except Exception as e:
            self.logger.error(f"Error retrieving readings for influence type {influence_type}: {str(e)}", exc_info=True)
            raise