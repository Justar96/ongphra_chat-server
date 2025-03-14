# app/services/meaning.py
from typing import Dict, List, Set

from app.domain.bases import Bases
from app.domain.meaning import Meaning, MeaningCollection
from app.repository.category_repository import CategoryRepository
from app.repository.reading_repository import ReadingRepository
from app.core.exceptions import MeaningExtractionError


class MeaningService:
    """Service for extracting meanings based on bases and question"""
    
    def __init__(
        self,
        category_repository: CategoryRepository,
        reading_repository: ReadingRepository
    ):
        """
        Initialize the meaning service
        
        Args:
            category_repository: Repository for categories
            reading_repository: Repository for readings
        """
        self.category_repository = category_repository
        self.reading_repository = reading_repository
        
        # Pre-defined keyword map for topic identification
        self.keyword_map = {
            "RELATIONSHIP": [
                "love", "relationship", "partner", "marriage", 
                "รัก", "ความรัก", "คู่", "แต่งงาน", "คู่ครอง"
            ],
            "FINANCE": [
                "money", "finance", "wealth", "business", 
                "เงิน", "การเงิน", "ธุรกิจ", "ลงทุน", "ทรัพย์"
            ],
            "CAREER": [
                "job", "work", "career", "promotion", 
                "งาน", "อาชีพ", "เลื่อนตำแหน่ง", "การงาน"
            ],
            "HEALTH": [
                "health", "illness", "disease", 
                "สุขภาพ", "โรค", "เจ็บป่วย"
            ],
            "EDUCATION": [
                "study", "school", "education", "exam", 
                "เรียน", "การศึกษา", "สอบ", "โรงเรียน"
            ]
        }
    
    def identify_topics(self, question: str) -> Set[str]:
        """Identify relevant topics based on the question"""
        question_lower = question.lower()
        topics = set()
        
        # Check for keywords in the question
        for category, keywords in self.keyword_map.items():
            if any(keyword in question_lower for keyword in keywords):
                topics.add(category)
        
        # Default to general readings if no specific category is identified
        if not topics:
            topics.add("GENERAL")
            topics.add("PERSONALITY")
            
        return topics
    
    async def get_category_ids(self, topics: Set[str]) -> List[int]:
        """Get category IDs based on topics"""
        category_ids = []
        
        for topic in topics:
            category = await self.category_repository.get_by_name(topic)
            if category:
                category_ids.append(category.id)
                
        return category_ids
    
    async def extract_meanings(self, bases: Bases, question: str) -> MeaningCollection:
        """
        Extract relevant meanings based on the bases and question
        Returns a collection of meanings with context
        """
        try:
            # Identify topics from question
            topics = self.identify_topics(question)
            
            # Get category IDs
            category_ids = await self.get_category_ids(topics)
            
            # Get relevant readings
            readings = await self.reading_repository.get_by_categories(category_ids)
            
            # Map readings to meanings
            meanings = []
            base_keys = ["base1", "base2", "base3", "base4"]
            
            for reading in readings:
                base_idx = reading.base
                if base_idx > 4:  # Only use bases 1-4 for now
                    continue
                    
                position = reading.position
                if position < 1 or position > 7:
                    continue
                
                # Get value from appropriate base
                base_key = base_keys[base_idx - 1]
                base_sequence = getattr(bases, base_key)
                value = base_sequence[position - 1] if position <= len(base_sequence) else 0
                
                # Create meaning object
                meaning = Meaning(
                    base=base_idx,
                    position=position,
                    value=value,
                    heading=reading.heading,
                    meaning=reading.meaning,
                    category=reading.category
                )
                
                meanings.append(meaning)
            
            return MeaningCollection(items=meanings)
            
        except Exception as e:
            raise MeaningExtractionError(f"Error extracting meanings: {str(e)}")