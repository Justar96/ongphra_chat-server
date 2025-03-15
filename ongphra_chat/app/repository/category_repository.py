# app/repository/category_repository.py
from typing import List, Optional

from app.repository.csv_repository import CSVRepository
from app.domain.meaning import Category
from app.core.logging import get_logger


class CategoryRepository(CSVRepository[Category]):
    """Repository for categories"""
    
    def __init__(self, file_path: str, model_class=Category):
        """Initialize the category repository"""
        super().__init__(file_path, model_class)
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initialized CategoryRepository with file: {file_path}")
    
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        self.logger.debug(f"Getting category by name: '{name}'")
        try:
            rows = self.df[self.df['category_name'] == name]
            if rows.empty:
                self.logger.debug(f"No category found with name: '{name}'")
                return None
            category = self.model_class(**rows.iloc[0].to_dict())
            self.logger.debug(f"Found category: {category.id} - {category.category_name}")
            return category
        except Exception as e:
            self.logger.error(f"Error retrieving category by name '{name}': {str(e)}", exc_info=True)
            raise
    
    async def get_by_thai_name(self, thai_name: str) -> Optional[Category]:
        """Get category by Thai name"""
        self.logger.debug(f"Getting category by Thai name: '{thai_name}'")
        try:
            rows = self.df[self.df['category_thai_name'] == thai_name]
            if rows.empty:
                self.logger.debug(f"No category found with Thai name: '{thai_name}'")
                return None
            category = self.model_class(**rows.iloc[0].to_dict())
            self.logger.debug(f"Found category: {category.id} - {category.category_thai_name}")
            return category
        except Exception as e:
            self.logger.error(f"Error retrieving category by Thai name '{thai_name}': {str(e)}", exc_info=True)
            raise
            
    async def create_category(self, category: Category) -> Category:
        """Create a new category"""
        self.logger.info(f"Creating new category: {category.category_name}")
        try:
            # Check if category with same name already exists
            existing = await self.get_by_name(category.category_name)
            if existing:
                self.logger.warning(f"Category with name '{category.category_name}' already exists")
                return existing
                
            # Save the category
            result = await self.save(category)
            self.logger.info(f"Successfully created category: {result.id} - {result.category_name}")
            return result
        except Exception as e:
            self.logger.error(f"Error creating category '{category.category_name}': {str(e)}", exc_info=True)
            raise
