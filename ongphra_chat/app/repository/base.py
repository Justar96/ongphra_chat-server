# app/repository/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generic, TypeVar

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Abstract base repository"""
    
    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[T]:
        """Get all entities"""
        pass
        
    @abstractmethod
    async def filter(self, **kwargs) -> List[T]:
        """Filter entities by criteria"""
        pass
        