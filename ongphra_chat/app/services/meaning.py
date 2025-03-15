# app/services/meaning.py
from typing import Dict, List, Set

from app.domain.bases import Bases
from app.domain.meaning import Meaning, MeaningCollection
from app.repository.category_repository import CategoryRepository
from app.repository.reading_repository import ReadingRepository
from app.core.exceptions import MeaningExtractionError
from app.core.logging import get_logger


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
        self.logger = get_logger(__name__)
        self.logger.info("Initialized MeaningService")
        
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
        self.logger.debug(f"Initialized keyword map with {len(self.keyword_map)} categories")
    
    def identify_topics(self, question: str) -> Set[str]:
        """Identify relevant topics based on the question"""
        self.logger.debug(f"Identifying topics for question: '{question}'")
        question_lower = question.lower()
        topics = set()
        
        # Check for keywords in the question
        for category, keywords in self.keyword_map.items():
            if any(keyword in question_lower for keyword in keywords):
                topics.add(category)
                self.logger.debug(f"Matched category: {category}")
        
        # Default to general readings if no specific category is identified
        if not topics:
            topics.add("GENERAL")
            topics.add("PERSONALITY")
            self.logger.debug("No specific topics identified, using default categories")
            
        self.logger.info(f"Identified topics: {', '.join(topics)}")
        return topics
    
    async def get_category_ids(self, topics: Set[str]) -> List[int]:
        """Get category IDs based on topics"""
        self.logger.debug(f"Getting category IDs for topics: {topics}")
        category_ids = []
        
        for topic in topics:
            category = await self.category_repository.get_by_name(topic)
            if category:
                category_ids.append(category.id)
                self.logger.debug(f"Found category ID {category.id} for topic {topic}")
            else:
                self.logger.warning(f"No category found for topic: {topic}")
                
        self.logger.info(f"Retrieved {len(category_ids)} category IDs: {category_ids}")
        return category_ids
    
    async def extract_meanings(self, bases: Bases, question: str) -> MeaningCollection:
        """
        Extract relevant meanings based on the bases and question
        Returns a collection of meanings with context
        """
        self.logger.info(f"Extracting meanings for question: '{question}'")
        try:
            # Identify topics from question
            topics = self.identify_topics(question)
            
            # Get category IDs
            category_ids = await self.get_category_ids(topics)
            
            # Get relevant readings
            self.logger.debug(f"Fetching readings for category IDs: {category_ids}")
            readings = await self.reading_repository.get_by_categories(category_ids)
            self.logger.info(f"Found {len(readings)} relevant readings")
            
            # Map readings to meanings
            meanings = []
            base_keys = ["base1", "base2", "base3", "base4"]
            
            for reading in readings:
                base_idx = reading.base
                if base_idx > 4:  # Only use bases 1-4 for now
                    self.logger.debug(f"Skipping reading with base {base_idx} (only using bases 1-4)")
                    continue
                    
                position = reading.position
                if position < 1 or position > 7:
                    self.logger.debug(f"Skipping reading with invalid position {position}")
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
                self.logger.debug(f"Added meaning: Base {base_idx}, Position {position}, Value {value}")
            
            result = MeaningCollection(items=meanings)
            self.logger.info(f"Extracted {len(meanings)} meanings for question")
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting meanings: {str(e)}", exc_info=True)
            raise MeaningExtractionError(f"Error extracting meanings: {str(e)}")