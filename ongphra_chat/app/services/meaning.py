# app/services/meaning.py
from typing import Dict, List, Set, Optional
import re

from app.domain.bases import Bases
from app.domain.meaning import Meaning, MeaningCollection, Category, Reading
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
                "love", "relationship", "partner", "marriage", "spouse", "dating",
                "รัก", "ความรัก", "คู่", "แต่งงาน", "คู่ครอง", "สามี", "ภรรยา", "แฟน", "จีบ"
            ],
            "FINANCE": [
                "money", "finance", "wealth", "business", "investment", "income", "debt",
                "เงิน", "การเงิน", "ธุรกิจ", "ลงทุน", "ทรัพย์", "รายได้", "หนี้", "กู้", "เงินกู้"
            ],
            "CAREER": [
                "job", "work", "career", "promotion", "business", "profession", "company",
                "งาน", "อาชีพ", "เลื่อนตำแหน่ง", "การงาน", "ตำแหน่ง", "บริษัท", "ธุรกิจ"
            ],
            "HEALTH": [
                "health", "illness", "disease", "wellness", "medical", "hospital", "doctor", 
                "สุขภาพ", "โรค", "เจ็บป่วย", "ป่วย", "หมอ", "โรงพยาบาล", "แข็งแรง"
            ],
            "EDUCATION": [
                "study", "school", "education", "exam", "university", "college", "course", "degree",
                "เรียน", "การศึกษา", "สอบ", "โรงเรียน", "มหาวิทยาลัย", "วิชา", "ปริญญา"
            ],
            "TRAVEL": [
                "travel", "journey", "trip", "vacation", "abroad", "overseas", "country",
                "เดินทาง", "ท่องเที่ยว", "ทริป", "ต่างประเทศ", "ต่างถิ่น", "พักผ่อน"
            ],
            "PERSONALITY": [
                "personality", "character", "trait", "strength", "weakness", "nature",
                "นิสัย", "บุคลิก", "ลักษณะ", "จุดแข็ง", "จุดอ่อน", "ธรรมชาติ"
            ]
        }
        self.logger.debug(f"Initialized keyword map with {len(self.keyword_map)} categories")
        
        # Initialize meaning cache
        self._meaning_cache = {}
    
    def identify_topics(self, question: str) -> Set[str]:
        """Identify relevant topics based on the question"""
        if not question:
            return {"GENERAL", "PERSONALITY"}
            
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
            try:
                category = await self.category_repository.get_by_name(topic)
                if category:
                    category_ids.append(category.id)
                    self.logger.debug(f"Found category ID {category.id} for topic {topic}")
                else:
                    self.logger.warning(f"No category found for topic: {topic}")
            except Exception as e:
                self.logger.error(f"Error getting category for topic {topic}: {str(e)}")
                # Continue with other topics instead of failing entirely
                
        self.logger.info(f"Retrieved {len(category_ids)} category IDs: {category_ids}")
        return category_ids
    
    def _get_cache_key(self, bases: Bases, question: str) -> str:
        """Generate a cache key from bases and question"""
        return (
            f"{str(bases.base1)}-{str(bases.base2)}-{str(bases.base3)}-{str(bases.base4)}"
            f"-{question}"
        )
    
    async def extract_meanings(self, bases: Bases, question: str) -> MeaningCollection:
        """
        Extract relevant meanings based on the bases and question
        Returns a collection of meanings with context
        """
        # Generate cache key
        cache_key = self._get_cache_key(bases, question)
        
        # Check cache
        if cache_key in self._meaning_cache:
            self.logger.info(f"Using cached meanings for question: '{question}'")
            return self._meaning_cache[cache_key]
            
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
                try:
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
                    
                    # Get category name
                    category_name = None
                    if reading.relationship_id:
                        try:
                            category = await self.category_repository.get_by_id(reading.relationship_id)
                            if category:
                                category_name = category.category_name
                        except Exception as e:
                            self.logger.warning(f"Error getting category for ID {reading.relationship_id}: {str(e)}")
                    
                    # Create meaning object
                    meaning = Meaning(
                        base=base_idx,
                        position=position,
                        value=value,
                        heading=reading.heading if hasattr(reading, 'heading') else f"Base {base_idx} Position {position}",
                        meaning=reading.content,
                        category=category_name or reading.category
                    )
                    
                    meanings.append(meaning)
                    self.logger.debug(f"Added meaning: Base {base_idx}, Position {position}, Value {value}")
                except Exception as item_error:
                    self.logger.warning(f"Error processing reading {reading.id}: {str(item_error)}")
                    # Continue with other readings
            
            result = MeaningCollection(items=meanings)
            self.logger.info(f"Extracted {len(meanings)} meanings for question")
            
            # Store in cache - only keep up to 100 items
            if len(self._meaning_cache) >= 100:
                # Remove oldest item
                oldest_key = next(iter(self._meaning_cache))
                del self._meaning_cache[oldest_key]
                
            self._meaning_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting meanings: {str(e)}", exc_info=True)
            raise MeaningExtractionError(f"Error extracting meanings: {str(e)}")
            
    async def get_meaning_by_base_position(self, base: int, position: int, bases: Bases) -> Optional[Meaning]:
        """Get a specific meaning by base and position"""
        try:
            if base < 1 or base > 4 or position < 1 or position > 7:
                self.logger.warning(f"Invalid base {base} or position {position}")
                return None
                
            # Get readings for this base and position
            readings = await self.reading_repository.get_by_base_and_position(base, position)
            
            if not readings:
                self.logger.warning(f"No readings found for base {base}, position {position}")
                return None
                
            # Use the first reading
            reading = readings[0]
            
            # Get the value from the corresponding base
            base_keys = ["base1", "base2", "base3", "base4"]
            base_key = base_keys[base - 1]
            base_sequence = getattr(bases, base_key)
            value = base_sequence[position - 1] if position <= len(base_sequence) else 0
            
            # Create and return meaning
            meaning = Meaning(
                base=base,
                position=position,
                value=value,
                heading=reading.heading if hasattr(reading, 'heading') else f"Base {base} Position {position}",
                meaning=reading.content,
                category=reading.category
            )
            
            return meaning
        
        except Exception as e:
            self.logger.error(f"Error getting meaning for base {base}, position {position}: {str(e)}")
            return None