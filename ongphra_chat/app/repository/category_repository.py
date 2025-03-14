# app/repository/category_repository.py
from typing import List, Optional

from app.repository.csv_repository import CSVRepository
from app.domain.meaning import Category


class CategoryRepository(CSVRepository[Category]):
    """Repository for categories"""
    
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        rows = self.df[self.df['category_name'] == name]
        if rows.empty:
            return None
        return self.model_class(**rows.iloc[0].to_dict())
    
    async def get_by_thai_name(self, thai_name: str) -> Optional[Category]:
        """Get category by Thai name"""
        rows = self.df[self.df['category_thai_name'] == thai_name]
        if rows.empty:
            return None
        return self.model_class(**rows.iloc[0].to_dict())
