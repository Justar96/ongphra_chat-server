# app/domain/response.py
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from app.domain.birth import BirthInfo
from app.domain.bases import Bases
from app.domain.meaning import MeaningCollection


class FortuneResponse(BaseModel):
    """Fortune response model"""
    fortune: str
    bases: Optional[Bases] = None
    birth_info: Optional[BirthInfo] = None
    meanings: Optional[MeaningCollection] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            "fortune": self.fortune
        }
        
        if self.bases:
            result["bases"] = self.bases.to_dict()
            
        if self.birth_info:
            result["birth_info"] = self.birth_info.to_dict()
            
        if self.meanings:
            result["meanings"] = self.meanings.to_dict()
            
        return result