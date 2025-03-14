# app/domain/birth.py
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel


class BirthInfo(BaseModel):
    """Birth information model"""
    date: datetime
    day: str
    day_value: int
    month: int
    year_animal: str
    year_start_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "day": self.day,
            "day_value": self.day_value,
            "month": self.month,
            "year_animal": self.year_animal,
            "year_start_number": self.year_start_number
        }