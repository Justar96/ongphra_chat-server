# app/services/reading_service.py
from typing import Dict, List, Optional, Tuple, Any
import re
from fastapi import Depends
from datetime import datetime

from app.domain.bases import BasesResult
from app.domain.meaning import Reading, Category, MeaningCollection, Meaning, FortuneReading
from app.repository.reading_repository import ReadingRepository
from app.repository.category_repository import CategoryRepository
from app.core.logging import get_logger
from app.core.exceptions import ReadingError
from app.services.calculator import CalculatorService
from app.services.session_service import get_session_manager


class ReadingService:
    """Service for extracting and matching readings from calculator results"""
    
    def __init__(
        self,
        reading_repository: ReadingRepository,
        category_repository: CategoryRepository
    ):
        """Initialize the reading service with repositories"""
        self.reading_repository = reading_repository
        self.category_repository = category_repository
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Initialized ReadingService")
        
        # Compile regex patterns for performance
        self.element_pattern = re.compile(r'\(([^)]+)\)')
        
        # Cache for category lookups
        self._category_cache = {}
    
    async def extract_elements_from_heading(self, heading: str) -> Tuple[str, str]:
        """
        Extract element names from a reading heading
        
        Example: "สินทรัพย์ (โภคา) สัมพันธ์กับ เพื่อนฝูง การติดต่อ (สหัชชะ)"
        Returns: ("โภคา", "สหัชชะ")
        """
        self.logger.debug(f"Extracting elements from heading: {heading}")
        
        if not heading:
            return ("", "")
            
        # Extract elements in parentheses using compiled regex
        elements = self.element_pattern.findall(heading)
        
        if len(elements) < 2:
            self.logger.warning(f"Could not extract two elements from heading: {heading}")
            return ("", "")
        
        # Return the first two elements found
        return (elements[0], elements[1])
    
    async def get_category_by_element_name(self, element_name: str) -> Optional[Category]:
        """Get category by element name, with caching"""
        if not element_name:
            return None
            
        # Check cache first
        if element_name in self._category_cache:
            return self._category_cache[element_name]
            
        self.logger.debug(f"Looking up category for element name: {element_name}")
        
        # First try to find by category_name
        category = await self.category_repository.get_by_name(element_name)
        
        # If not found, try by thai_name
        if not category:
            self.logger.debug(f"Category not found by name, trying Thai name: {element_name}")
            category = await self.category_repository.get_by_thai_name(element_name)
        
        if not category:
            self.logger.warning(f"No category found for element name: {element_name}")
        else:
            self.logger.debug(f"Found category: {category.id} - {category.category_name}")
            # Add to cache
            self._category_cache[element_name] = category
            
        return category
    
    async def get_readings_for_base_position(self, base: int, position: int) -> List[Reading]:
        """
        Get readings for a specific base and position
        
        Args:
            base: Base number (1-4)
            position: Position number (1-7)
            
        Returns:
            List of readings that match the base and position
        """
        self.logger.debug(f"Getting readings for base {base}, position {position}")
        
        # Define Thai position names for each base
        thai_positions = {
            1: ['อัตตะ', 'หินะ', 'ธานัง', 'ปิตา', 'มาตา', 'โภคา', 'มัชฌิมา'],  # Base 1 (Day)
            2: ['ตะนุ', 'กดุมภะ', 'สหัชชะ', 'พันธุ', 'ปุตตะ', 'อริ', 'ปัตนิ'],  # Base 2 (Month)
            3: ['มรณะ', 'สุภะ', 'กัมมะ', 'ลาภะ', 'พยายะ', 'ทาสา', 'ทาสี'],    # Base 3 (Year)
        }
        
        try:
            # Get the Thai position name if available
            thai_position_name = ""
            if base < 4 and position <= len(thai_positions[base]):
                thai_position_name = thai_positions[base][position - 1]  # Convert to 0-indexed for array access
                self.logger.debug(f"Base {base}, Position {position} corresponds to '{thai_position_name}'")
            
            # Try to get readings in two ways:
            
            # 1. First, try to get by house_number
            readings = await self.reading_repository.get_by_base_and_position(base, position)
            
            # 2. If no readings found and we have a Thai position name, try by category name
            if not readings and thai_position_name:
                # Get the category for this Thai position
                category = await self.get_category_by_element_name(thai_position_name)
                if category:
                    self.logger.debug(f"Found category {category.id} for '{thai_position_name}', querying readings by category")
                    readings = await self.reading_repository.get_by_categories([category.id])
            
            self.logger.debug(f"Found {len(readings)} readings for base {base}, position {position}")
            return readings
        except Exception as e:
            self.logger.error(f"Error getting readings for base {base}, position {position}: {str(e)}")
            raise ReadingError(f"Failed to get readings: {str(e)}")
    
    async def extract_meanings_from_calculator_result(
        self, 
        bases_result: BasesResult
    ) -> MeaningCollection:
        """
        Extract meanings from calculator result by matching base values with readings
        and using the Thai position names to query the database
        
        In Thai astrology, each base (ฐาน) corresponds to a house_number in the database:
        - Base 1 (ฐานที่ 1): Represents the day of birth and maps to house_number 1
        - Base 2 (ฐานที่ 2): Represents the month and maps to house_number 2
        - Base 3 (ฐานที่ 3): Represents the year and maps to house_number 3
        - Base 4 (ฐานที่ 4): Represents the sum of bases 1-3 and maps to house_number 4
        
        Each position (1-7) in a base maps to a specific Thai category name:
        Base 1: ['อัตตะ', 'หินะ', 'ธานัง', 'ปิตา', 'มาตา', 'โภคา', 'มัชฌิมา']
        Base 2: ['ตะนุ', 'กดุมภะ', 'สหัชชะ', 'พันธุ', 'ปุตตะ', 'อริ', 'ปัตนิ']  
        Base 3: ['มรณะ', 'สุภะ', 'กัมมะ', 'ลาภะ', 'พยายะ', 'ทาสา', 'ทาสี']
        """
        self.logger.info("Extracting meanings from calculator result")
        
        if not bases_result or not bases_result.bases:
            self.logger.error("Invalid calculator result: missing bases")
            raise ReadingError("Invalid calculator result: missing bases")
            
        meanings = []
        
        # Define Thai position names for each base
        thai_positions = {
            1: ['อัตตะ', 'หินะ', 'ธานัง', 'ปิตา', 'มาตา', 'โภคา', 'มัชฌิมา'],  # Base 1 (Day)
            2: ['ตะนุ', 'กดุมภะ', 'สหัชชะ', 'พันธุ', 'ปุตตะ', 'อริ', 'ปัตนิ'],  # Base 2 (Month)
            3: ['มรณะ', 'สุภะ', 'กัมมะ', 'ลาภะ', 'พยายะ', 'ทาสา', 'ทาสี'],    # Base 3 (Year)
        }
        
        # Process each base (1-4)
        for base_num in range(1, 5):
            base_attr = f"base{base_num}"
            
            if not hasattr(bases_result.bases, base_attr):
                self.logger.warning(f"Base {base_num} not found in calculator result")
                continue
                
            base_values = getattr(bases_result.bases, base_attr)
            
            if not base_values or len(base_values) != 7:
                self.logger.warning(f"Invalid values for base {base_num}: {base_values}")
                continue
            
            # Process each position (0-6)
            for position in range(7):
                try:
                    value = base_values[position]
                    position_num = position + 1  # Convert to 1-indexed for database
                    
                    # Get the Thai position name
                    thai_position_name = ""
                    if base_num < 4 and position < len(thai_positions[base_num]):
                        thai_position_name = thai_positions[base_num][position]
                        self.logger.debug(f"Position {position_num} in Base {base_num} corresponds to '{thai_position_name}'")
                    
                    # Get readings for this base and position
                    readings = await self.get_readings_for_base_position(base_num, position_num)
                    
                    for reading in readings:
                        try:
                            # Get the category for this Thai position
                            category = None
                            if thai_position_name:
                                category = await self.get_category_by_element_name(thai_position_name)
                            
                            # Extract elements from heading for additional information
                            element1, element2 = await self.extract_elements_from_heading(
                                reading.heading if hasattr(reading, 'heading') else ""
                            )
                            
                            # Create category string
                            category_str = ""
                            if category:
                                category_str = category.category_name
                            elif hasattr(reading, 'category') and reading.category:
                                category_str = reading.category
                            
                            # If we can extract elements from the heading, use them as additional information
                            category1 = await self.get_category_by_element_name(element1)
                            category2 = await self.get_category_by_element_name(element2)
                            
                            if category1 and category2:
                                if category_str:
                                    category_str += f" ({category1.category_name} - {category2.category_name})"
                                else:
                                    category_str = f"{category1.category_name} - {category2.category_name}"
                            elif category1:
                                if category_str:
                                    category_str += f" ({category1.category_name})"
                                else:
                                    category_str = category1.category_name
                            elif category2:
                                if category_str:
                                    category_str += f" ({category2.category_name})"
                                else:
                                    category_str = category2.category_name
                            
                            # Calculate match score based on relevance to the base value
                            match_score = self._calculate_match_score(base_num, position_num, value)
                            
                            # Create meaning object
                            meaning = Meaning(
                                base=base_num,
                                position=position_num,
                                value=value,
                                heading=reading.heading if hasattr(reading, 'heading') else f"Base {base_num} Position {position_num}",
                                meaning=reading.content if hasattr(reading, 'content') else reading.thai_content if hasattr(reading, 'thai_content') else "",
                                category=category_str,
                                match_score=match_score
                            )
                            
                            meanings.append(meaning)
                            self.logger.debug(f"Added meaning for Base {base_num}, Position {position_num}, Category: {category_str}")
                        except Exception as reading_error:
                            self.logger.warning(f"Error processing reading {reading.id if hasattr(reading, 'id') else 'unknown'}: {str(reading_error)}")
                            # Continue with other readings
                except Exception as position_error:
                    self.logger.warning(f"Error processing base {base_num}, position {position}: {str(position_error)}")
                    # Continue with other positions
        
        # Sort meanings by match score (if available)
        meanings.sort(key=lambda m: getattr(m, 'match_score', 0), reverse=True)
        
        # Limit to a reasonable number of meanings
        if len(meanings) > 20:
            meanings = meanings[:20]
        
        self.logger.info(f"Extracted {len(meanings)} meanings from calculator result")
        return MeaningCollection(items=meanings)
    
    def _calculate_match_score(self, base: int, position: int, value: int) -> float:
        """
        Calculate a match score (0-10) based on the base, position, and value
        This is a simple algorithm that can be refined over time
        """
        # Base score starts at 5
        score = 5.0
        
        # Add points for important bases
        if base == 1:  # Base 1 is usually important for personality
            score += 1.0
        elif base == 4:  # Base 4 often indicates future trends
            score += 0.5
            
        # Add points based on value - values 1, 5, 7 are often considered significant
        if value in [1, 5, 7]:
            score += 1.0
        elif value in [3, 6]:  # Also somewhat significant
            score += 0.5
            
        # Add points for central positions (more significant)
        if position in [3, 4, 5]:
            score += 0.5
            
        # Make sure score is between 0 and 10
        return max(0.0, min(10.0, score))
    
    async def get_fortune_reading(
        self,
        birth_date: datetime,
        thai_day: Optional[str] = None,
        question: Optional[str] = None,
        user_id: str = "default_user" 
    ) -> FortuneReading:
        """
        Get a fortune reading based on birth date and Thai day
        
        This method follows the correct flow:
        1. Calculate the bases using the calculator service
        2. Use the bases to find the appropriate ภพ (house/base)
        3. Query the database based on those values
        4. If there's a question, try to find the most relevant reading using session context
        5. Return a formatted reading
        """
        self.logger.info(f"Getting fortune reading for birth_date={birth_date}, thai_day={thai_day}, user_id={user_id}")
        
        try:
            # Get session manager for tracking
            session_manager = get_session_manager()
            
            # Step 1: Calculate bases from birth info
            calculator = CalculatorService()
            calculation_result = calculator.calculate_birth_bases(birth_date, thai_day)
            
            # If thai_day wasn't provided, get it from the calculation result
            if not thai_day:
                thai_day = calculation_result.birth_info.day
            
            # Save birth info in the session
            session_manager.save_birth_info(user_id, birth_date, thai_day)
            
            # Step 2: Extract meanings from the calculation result
            meanings_collection = await self.extract_meanings_from_calculator_result(calculation_result)
            
            # Step 3: Select the most relevant reading based on the question or highest match score
            selected_meaning = None
            
            if meanings_collection.items:
                if not question:
                    # If no question, just use the highest scored meaning
                    selected_meaning = meanings_collection.items[0]
                    self.logger.info(f"No question provided, using highest scored meaning")
                else:
                    # Define topic keywords to help match questions to readings
                    topic_mappings = {
                        'การเงิน': ['เงิน', 'ทรัพย์', 'รายได้', 'ธุรกิจ', 'การเงิน', 'เศรษฐกิจ', 'ค้าขาย', 'ลงทุน', 'หุ้น', 'กำไร', 'ขาดทุน'],
                        'ความรัก': ['รัก', 'แฟน', 'คู่ครอง', 'สามี', 'ภรรยา', 'แต่งงาน', 'หมั้น', 'จีบ', 'ความสัมพันธ์', 'คนรัก', 'รักใคร่'],
                        'สุขภาพ': ['สุขภาพ', 'ป่วย', 'โรค', 'หมอ', 'รักษา', 'ผ่าตัด', 'ยา', 'แข็งแรง', 'ร่างกาย', 'จิตใจ', 'การรักษา'],
                        'การงาน': ['งาน', 'อาชีพ', 'เลื่อนตำแหน่ง', 'เงินเดือน', 'หัวหน้า', 'ลูกน้อง', 'บริษัท', 'องค์กร', 'สมัครงาน', 'ตำแหน่ง'],
                        'การศึกษา': ['เรียน', 'สอบ', 'โรงเรียน', 'มหาวิทยาลัย', 'วิชา', 'การศึกษา', 'ปริญญา', 'จบ', 'วิทยาลัย', 'นักเรียน'],
                        'ครอบครัว': ['ครอบครัว', 'พ่อ', 'แม่', 'ลูก', 'พี่', 'น้อง', 'ญาติ', 'บ้าน', 'ครอบครัว', 'ชีวิตครอบครัว'],
                        'โชคลาภ': ['โชค', 'ลาภ', 'หวย', 'ล็อตเตอรี่', 'ถูกรางวัล', 'ดวง', 'โชคลาภ', 'เสี่ยงโชค', 'สลาก'],
                        'อนาคต': ['อนาคต', 'ชะตา', 'ดวงชะตา', 'คำทำนาย', 'โหราศาสตร์', 'ชีวิต', 'ลิขิต', 'เคราะห์'],
                        'การเดินทาง': ['เดินทาง', 'ท่องเที่ยว', 'ต่างประเทศ', 'ต่างถิ่น', 'ทริป', 'ย้ายถิ่นฐาน', 'ย้ายบ้าน', 'ย้ายที่อยู่']
                    }
                    
                    # Get conversation history for better context
                    conversation_history = session_manager.get_conversation_history(user_id)
                    conversation_text = " ".join([msg["content"] for msg in conversation_history])
                    
                    # Combine question with conversation context for better matching
                    full_context = f"{question} {conversation_text}"
                    
                    # Try to match the question to a topic
                    matched_topic = None
                    max_matches = 0
                    
                    for topic, keywords in topic_mappings.items():
                        # Count how many keywords match in the context
                        match_count = sum(1 for keyword in keywords if keyword in full_context.lower())
                        if match_count > max_matches:
                            max_matches = match_count
                            matched_topic = topic
                    
                    if matched_topic:
                        # Save the matched topic to session
                        session_manager.save_topic(user_id, matched_topic)
                        
                        self.logger.info(f"Question matched to topic: {matched_topic} (match score: {max_matches})")
                        
                        # Find meanings that might be related to this topic
                        matching_meanings = []
                        for meaning in meanings_collection.items:
                            # Check if the meaning category or heading contains keywords related to the topic
                            meaning_text = f"{meaning.category} {meaning.heading} {meaning.meaning}"
                            match_score = sum(1 for keyword in topic_mappings[matched_topic] if keyword in meaning_text.lower())
                            
                            if match_score > 0:
                                # Add the match score to the existing match score
                                meaning.match_score += match_score * 0.5  # Weight topic match less than astrology match
                                matching_meanings.append(meaning)
                        
                        if matching_meanings:
                            # Sort by match score and use the highest
                            matching_meanings.sort(key=lambda m: getattr(m, 'match_score', 0), reverse=True)
                            selected_meaning = matching_meanings[0]
                            self.logger.info(f"Found relevant meaning for topic {matched_topic}: {selected_meaning.heading}")
                        else:
                            # No topic-specific meaning found, use the highest scored meaning
                            selected_meaning = meanings_collection.items[0]
                            self.logger.info(f"No meaning found for topic {matched_topic}, using highest scored meaning")
                            
                        # Consider previous topics for continuity
                        previous_topics = session_manager.get_recent_topics(user_id)
                        if previous_topics and matched_topic not in previous_topics:
                            self.logger.info(f"User has asked about different topics: {previous_topics} -> {matched_topic}")
                            # We could adjust the response here to note the change in topic
                    else:
                        # No topic matched, use the highest scored meaning
                        selected_meaning = meanings_collection.items[0]
                        self.logger.info(f"Question does not match any specific topic, using highest scored meaning")
                        
                    # Save calculation result in session for future reference
                    session_manager.save_context_data(user_id, "last_calculation", {
                        "birth_date": birth_date.strftime("%Y-%m-%d"),
                        "thai_day": thai_day,
                        "bases": {
                            "base1": calculation_result.bases.base1,
                            "base2": calculation_result.bases.base2,
                            "base3": calculation_result.bases.base3,
                            "base4": calculation_result.bases.base4
                        }
                    })
            
            # Step 4: Create the fortune reading response
            if selected_meaning:
                # Determine influence type based on meaning content if available
                influence_type = "ดี"  # Default to positive
                if hasattr(selected_meaning, 'influence_type') and selected_meaning.influence_type:
                    influence_type = selected_meaning.influence_type
                
                reading = FortuneReading(
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day,
                    question=question,
                    heading=selected_meaning.heading,
                    meaning=selected_meaning.meaning,
                    influence_type=influence_type
                )
                
                # Save the reading to the session
                session_manager.save_context_data(user_id, "last_reading", {
                    "heading": selected_meaning.heading,
                    "category": selected_meaning.category if hasattr(selected_meaning, 'category') else "",
                    "base": selected_meaning.base,
                    "position": selected_meaning.position,
                    "value": selected_meaning.value
                })
                
                self.logger.info(f"Created fortune reading with heading: {reading.heading}")
                return reading
            else:
                # Fallback if no meanings found
                self.logger.warning("No meanings found, returning generic reading")
                return FortuneReading(
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day,
                    question=question,
                    heading="ไม่พบข้อมูลที่เกี่ยวข้อง",
                    meaning="ไม่สามารถวิเคราะห์ข้อมูลได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง",
                    influence_type="ปานกลาง"
                )
                
        except Exception as e:
            self.logger.error(f"Error getting fortune reading: {str(e)}", exc_info=True)
            # Return error reading
            return FortuneReading(
                birth_date=birth_date.strftime("%Y-%m-%d") if birth_date else "",
                thai_day=thai_day if thai_day else "",
                question=question,
                heading="เกิดข้อผิดพลาด",
                meaning=f"เกิดข้อผิดพลาดในการวิเคราะห์: {str(e)}",
                influence_type="ไม่ทราบ"
            )


# Factory function for dependency injection
async def get_reading_service(
    reading_repository: ReadingRepository = Depends(),
    category_repository: CategoryRepository = Depends()
) -> ReadingService:
    """Get reading service instance"""
    return ReadingService(reading_repository, category_repository)