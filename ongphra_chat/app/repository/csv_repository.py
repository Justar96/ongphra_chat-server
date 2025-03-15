# app/repository/csv_repository.py
import pandas as pd
import os.path
from typing import List, Dict, Any, Optional, Type, TypeVar, Generic
from pydantic import BaseModel

from app.repository.base import BaseRepository
from app.core.logging import get_logger

T = TypeVar('T', bound=BaseModel)

class CSVRepository(BaseRepository[T]):
    """Repository implementation using CSV files"""
    
    def __init__(self, file_path: str, model_class: Type[T]):
        """
        Initialize the repository
        
        Args:
            file_path: Path to the CSV file
            model_class: Pydantic model class for the entity
        """
        self.file_path = file_path
        self.model_class = model_class
        self._df = None
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initialized CSV repository for {model_class.__name__} with file: {file_path}")
        
        # Log warning if file doesn't exist
        if not os.path.exists(file_path):
            self.logger.warning(f"CSV file not found: {file_path}")
    
    @property
    def df(self) -> pd.DataFrame:
        """Lazy load the dataframe"""
        if self._df is None:
            self.logger.info(f"Loading CSV data from {self.file_path}")
            try:
                if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
                    self._df = pd.read_csv(self.file_path)
                    self.logger.info(f"Successfully loaded {len(self._df)} rows from {self.file_path}")
                else:
                    self.logger.warning(f"CSV file is empty or does not exist: {self.file_path}")
                    self._df = pd.DataFrame()
                    self.logger.info(f"Created empty DataFrame for {self.file_path}")
            except Exception as e:
                self.logger.error(f"Error loading CSV file {self.file_path}: {str(e)}", exc_info=True)
                # Re-raise to maintain original behavior
                raise
        return self._df
    
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID"""
        self.logger.debug(f"Getting entity by ID: {id}")
        try:
            row = self.df[self.df['id'] == id]
            if row.empty:
                self.logger.debug(f"No entity found with ID: {id}")
                return None
            entity = self.model_class(**row.iloc[0].to_dict())
            self.logger.debug(f"Found entity with ID: {id}")
            return entity
        except Exception as e:
            self.logger.error(f"Error retrieving entity with ID {id}: {str(e)}", exc_info=True)
            raise
    
    async def get_all(self) -> List[T]:
        """Get all entities"""
        self.logger.debug(f"Getting all entities from {self.file_path}")
        try:
            entities = [self.model_class(**row.to_dict()) for _, row in self.df.iterrows()]
            self.logger.debug(f"Retrieved {len(entities)} entities")
            return entities
        except Exception as e:
            self.logger.error(f"Error retrieving all entities: {str(e)}", exc_info=True)
            raise
        
    async def filter(self, **kwargs) -> List[T]:
        """Filter entities by criteria"""
        self.logger.debug(f"Filtering entities with criteria: {kwargs}")
        try:
            query = True
            for key, value in kwargs.items():
                if key in self.df.columns:
                    query = query & (self.df[key] == value)
                else:
                    self.logger.warning(f"Filter key '{key}' not found in DataFrame columns")
            
            filtered_df = self.df[query]
            entities = [self.model_class(**row.to_dict()) for _, row in filtered_df.iterrows()]
            self.logger.debug(f"Filter returned {len(entities)} entities")
            return entities
        except Exception as e:
            self.logger.error(f"Error filtering entities with criteria {kwargs}: {str(e)}", exc_info=True)
            raise
            
    async def save(self, entity: T) -> T:
        """Save entity to CSV file"""
        self.logger.info(f"Saving entity to {self.file_path}")
        try:
            # Convert entity to dict
            entity_dict = entity.model_dump()
            
            # Create new dataframe with the entity
            new_row = pd.DataFrame([entity_dict])
            
            # If ID exists, update existing row
            if hasattr(entity, 'id') and entity.id is not None:
                self.logger.debug(f"Updating entity with ID: {entity.id}")
                # Check if entity with this ID already exists
                existing = self.df[self.df['id'] == entity.id]
                if not existing.empty:
                    # Update existing row
                    self._df = self.df[self.df['id'] != entity.id]
                    self._df = pd.concat([self._df, new_row], ignore_index=True)
                else:
                    # Append new row
                    self._df = pd.concat([self.df, new_row], ignore_index=True)
            else:
                self.logger.debug("Adding new entity")
                # Append new row
                self._df = pd.concat([self.df, new_row], ignore_index=True)
            
            # Save to CSV
            self._df.to_csv(self.file_path, index=False)
            self.logger.info(f"Successfully saved entity to {self.file_path}")
            
            return entity
        except Exception as e:
            self.logger.error(f"Error saving entity to {self.file_path}: {str(e)}", exc_info=True)
            raise
            
    async def delete(self, id: Any) -> bool:
        """Delete entity by ID"""
        self.logger.info(f"Deleting entity with ID: {id}")
        try:
            # Check if entity exists
            existing = self.df[self.df['id'] == id]
            if existing.empty:
                self.logger.warning(f"No entity found with ID: {id}")
                return False
            
            # Remove row with the specified ID
            self._df = self.df[self.df['id'] != id]
            
            # Save to CSV
            self._df.to_csv(self.file_path, index=False)
            self.logger.info(f"Successfully deleted entity with ID: {id}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error deleting entity with ID {id}: {str(e)}", exc_info=True)
            raise