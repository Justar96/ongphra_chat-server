# app/repository/csv_repository.py
import pandas as pd
from typing import List, Dict, Any, Optional, Type, TypeVar, Generic
from pydantic import BaseModel

from app.repository.base import BaseRepository

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
    
    @property
    def df(self) -> pd.DataFrame:
        """Lazy load the dataframe"""
        if self._df is None:
            self._df = pd.read_csv(self.file_path)
        return self._df
    
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID"""
        row = self.df[self.df['id'] == id]
        if row.empty:
            return None
        return self.model_class(**row.iloc[0].to_dict())
    
    async def get_all(self) -> List[T]:
        """Get all entities"""
        return [self.model_class(**row.to_dict()) for _, row in self.df.iterrows()]
        
    async def filter(self, **kwargs) -> List[T]:
        """Filter entities by criteria"""
        query = True
        for key, value in kwargs.items():
            if key in self.df.columns:
                query = query & (self.df[key] == value)
        
        filtered_df = self.df[query]
        return [self.model_class(**row.to_dict()) for _, row in filtered_df.iterrows()]