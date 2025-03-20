# app/domain/meaning.py
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Meaning(BaseModel):
    """Individual meaning model"""
    id: Optional[int] = None  # Make id optional
    base: int
    position: int
    value: int
    heading: str
    meaning: str
    category: Optional[str] = None
    match_score: float = 5.0  # Default value for match score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "id": self.id,
            "base": self.base,
            "position": self.position,
            "value": self.value,
            "heading": self.heading,
            "meaning": self.meaning,
            "category": self.category,
            "match_score": self.match_score
        }
    
    @property
    def description(self) -> str:
        """Get a formatted description of this meaning"""
        return f"{self.heading}: {self.meaning}"


class MeaningCollection(BaseModel):
    """Collection of meanings"""
    items: List[Meaning]
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert to dictionary for API response"""
        return [item.to_dict() for item in self.items]
    
    @property
    def base_meanings(self) -> Dict[str, List[Meaning]]:
        """
        Group meanings by base
        Returns a dictionary with base names as keys and lists of meanings as values
        """
        result = {}
        for item in self.items:
            base_name = f"Base {item.base}"
            if base_name not in result:
                result[base_name] = []
            result[base_name].append(item)
        return result


class Category(BaseModel):
    """Category model for readings"""
    id: int
    name: str
    thai_meaning: str
    house_number: int
    house_type: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @property
    def category_name(self) -> str:
        """Accessor for category_name for compatibility with code that uses this field"""
        return self.name


class CategoryCombination(BaseModel):
    """Category combination model"""
    id: int
    file_name: str
    category1_id: int
    category2_id: int
    category3_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class Reading(BaseModel):
    """Reading model for fortune telling"""
    id: int
    combination_id: int
    heading: str
    meaning: str
    influence_type: str
    file_name: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @property
    def content(self) -> str:
        """Accessor for content field for compatibility with code that uses this field"""
        return self.meaning
    
    @property
    def thai_content(self) -> str:
        """Accessor for thai_content field for compatibility with code that uses this field"""
        return self.meaning


class FortuneReading(BaseModel):
    """Fortune reading result model"""
    birth_date: str
    thai_day: str
    question: Optional[str] = None
    heading: str
    meaning: str
    influence_type: str
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "birth_date": self.birth_date,
            "thai_day": self.thai_day,
            "question": self.question,
            "heading": self.heading,
            "meaning": self.meaning,
            "influence_type": self.influence_type
        }
