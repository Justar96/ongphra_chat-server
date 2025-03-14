# app/domain/meaning.py
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class Meaning(BaseModel):
    """Individual meaning model"""
    base: int
    position: int
    value: int
    heading: str
    meaning: str
    category: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "base": self.base,
            "position": self.position,
            "value": self.value,
            "heading": self.heading,
            "meaning": self.meaning,
            "category": self.category
        }


class MeaningCollection(BaseModel):
    """Collection of meanings"""
    items: List[Meaning]
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert to dictionary for API response"""
        return [item.to_dict() for item in self.items]


class Category(BaseModel):
    """Category model for readings"""
    id: int
    category_name: str
    category_thai_name: str
    description: Optional[str] = None


class Reading(BaseModel):
    """Reading model for fortune telling"""
    id: int
    base: int
    position: int
    relationship_id: Optional[int] = None
    content: str
    thai_content: Optional[str] = None