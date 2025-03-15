# app/repository/reading_repository.py
from typing import List, Optional

from app.repository.csv_repository import CSVRepository
from app.domain.meaning import Reading
from app.core.logging import get_logger


class ReadingRepository(CSVRepository[Reading]):
    """Repository for readings"""
    
    def __init__(self, file_path: str, model_class=Reading):
        """Initialize the reading repository"""
        super().__init__(file_path, model_class)
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initialized ReadingRepository with file: {file_path}")
    
    async def get_by_base_and_position(self, base: int, position: int) -> List[Reading]:
        """Get readings by base and position"""
        self.logger.debug(f"Getting readings for base {base}, position {position}")
        try:
            readings = await self.filter(base=base, position=position)
            self.logger.debug(f"Found {len(readings)} readings for base {base}, position {position}")
            
            # Log detailed information about the readings at trace level
            for reading in readings:
                self.logger.debug(f"Reading details: Base {reading.base}, Position {reading.position}, ID {reading.id}, Relationship {reading.relationship_id}")
                
            return readings
        except Exception as e:
            self.logger.error(f"Error retrieving readings for base {base}, position {position}: {str(e)}", exc_info=True)
            raise
    
    async def get_by_categories(self, category_ids: List[int]) -> List[Reading]:
        """Get readings by category IDs"""
        if not category_ids:
            self.logger.warning("No category IDs provided for reading lookup")
            return []
            
        self.logger.debug(f"Getting readings for category IDs: {category_ids}")
        try:
            filtered_df = self.df[self.df['relationship_id'].isin(category_ids)]
            readings = [self.model_class(**row.to_dict()) for _, row in filtered_df.iterrows()]
            self.logger.debug(f"Found {len(readings)} readings for category IDs: {category_ids}")
            
            # Log detailed information about the readings at trace level
            for reading in readings:
                self.logger.debug(f"Reading: Base {reading.base}, Position {reading.position}, ID {reading.id}, Relationship {reading.relationship_id}")
                
            return readings
        except Exception as e:
            self.logger.error(f"Error retrieving readings for category IDs {category_ids}: {str(e)}", exc_info=True)
            raise
            
    async def create_reading(self, reading: Reading) -> Reading:
        """Create a new reading"""
        self.logger.info(f"Creating new reading for base {reading.base}, position {reading.position}")
        try:
            # Save the reading
            result = await self.save(reading)
            self.logger.info(f"Successfully created reading: ID {result.id}, Base {result.base}, Position {result.position}")
            return result
        except Exception as e:
            self.logger.error(f"Error creating reading for base {reading.base}, position {reading.position}: {str(e)}", exc_info=True)
            raise
            
    async def update_reading(self, reading: Reading) -> Reading:
        """Update an existing reading"""
        self.logger.info(f"Updating reading with ID {reading.id}")
        try:
            # Check if reading exists
            existing = await self.get_by_id(reading.id)
            if not existing:
                self.logger.warning(f"Reading with ID {reading.id} not found for update")
                raise ValueError(f"Reading with ID {reading.id} not found")
                
            # Save the updated reading
            result = await self.save(reading)
            self.logger.info(f"Successfully updated reading: ID {result.id}, Base {result.base}, Position {result.position}")
            return result
        except Exception as e:
            self.logger.error(f"Error updating reading with ID {reading.id}: {str(e)}", exc_info=True)
            raise