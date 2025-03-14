# app/repository/reading_repository.py
from typing import List

from app.repository.csv_repository import CSVRepository
from app.domain.meaning import Reading


class ReadingRepository(CSVRepository[Reading]):
    """Repository for readings"""
    
    async def get_by_base_and_position(self, base: int, position: int) -> List[Reading]:
        """Get readings by base and position"""
        return await self.filter(base=base, position=position)
    
    async def get_by_categories(self, category_ids: List[int]) -> List[Reading]:
        """Get readings by category IDs"""
        filtered_df = self.df[self.df['relationship_id'].isin(category_ids)]
        return [self.model_class(**row.to_dict()) for _, row in filtered_df.iterrows()]