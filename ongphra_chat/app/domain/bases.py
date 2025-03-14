# app/domain/bases.py
from typing import Dict, List, Any
from pydantic import BaseModel
from app.domain.birth import BirthInfo


class Bases(BaseModel):
    """Base sequences model"""
    base1: List[int]
    base2: List[int]
    base3: List[int]
    base4: List[int]
    
    def to_dict(self) -> Dict[str, List[int]]:
        """Convert to dictionary for API response"""
        return {
            "base1": self.base1,
            "base2": self.base2,
            "base3": self.base3,
            "base4": self.base4
        }


class BasesResult(BaseModel):
    """Combined result of birth info and bases calculation"""
    birth_info: BirthInfo
    bases: Bases
