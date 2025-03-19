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
from app.services.ai_topic_service import AITopicService


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
        
        self.calculator_service = CalculatorService()
        self.ai_topic_service = AITopicService()
    
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
    
    async def extract_meanings_from_calculator_result(self, calculator_result: BasesResult) -> List[Meaning]:
        """
        Extract meanings from calculator result
        
        Each position (1-7) in a base maps to a specific Thai category name:
        Base 1: ['อัตตะ', 'หินะ', 'ธานัง', 'ปิตา', 'มาตา', 'โภคา', 'มัชฌิมา']
        Base 2: ['ตะนุ', 'กดุมภะ', 'สหัชชะ', 'พันธุ', 'ปุตตะ', 'อริ', 'ปัตนิ']  
        Base 3: ['มรณะ', 'สุภะ', 'กัมมะ', 'ลาภะ', 'พยายะ', 'ทาสา', 'ทาสี']
        """
        self.logger.info("Extracting meanings from calculator result")
        
        if not calculator_result or not calculator_result.bases:
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
            
            if not hasattr(calculator_result.bases, base_attr):
                self.logger.warning(f"Base {base_num} not found in calculator result")
                continue
                
            base_values = getattr(calculator_result.bases, base_attr)
            
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
                            
                        except Exception as e:
                            self.logger.error(f"Error processing reading: {str(e)}")
                            continue
                            
                except Exception as e:
                    self.logger.error(f"Error processing position {position} in base {base_num}: {str(e)}")
                    continue
                    
        self.logger.info(f"Extracted {len(meanings)} meanings from calculator result")
        return meanings
    
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
        birth_date: Optional[datetime] = None,
        thai_day: Optional[str] = None,
        user_question: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> FortuneReading:
        """Get a fortune reading based on birth date and optional user question"""
        try:
            if not birth_date:
                return FortuneReading(
                    heading="กรุณาระบุวันเกิด",
                    meaning="ต้องการวันเกิดเพื่อทำนายดวงชะตา",
                    influence_type="ทั่วไป",
                    birth_date="",
                    thai_day=""
                )

            # Calculate bases using calculator service
            calculator_result = self.calculator_service.calculate_birth_bases(birth_date, thai_day)
            
            # Extract meanings from calculator result
            all_meanings = await self.extract_meanings_from_calculator_result(calculator_result)
            self.logger.info(f"Initially extracted {len(all_meanings)} meanings from calculator result")
            
            if not all_meanings:
                return FortuneReading(
                    heading="ไม่พบความหมาย",
                    meaning="ขออภัย ไม่พบความหมายที่เหมาะสม",
                    influence_type="ทั่วไป",
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day or calculator_result.thai_day
                )
                
            # Filter and rank meanings for more relevant results
            meanings = self._filter_and_rank_meanings(all_meanings, user_question)
            self.logger.info(f"Filtered to {len(meanings)} relevant meanings")

            # Detect topic using AI service if there's a question
            topic_result = None
            detected_topic = "ทั่วไป"  # Default topic
            
            if user_question:
                try:
                    # Detect topic using AI service
                    topic_result = await self.ai_topic_service.detect_topic(user_question)
                    detected_topic = topic_result['primary_topic']
                    self.logger.info(f"AI detected topic: {detected_topic} with confidence {topic_result['confidence']}")
                    
                    # Find meaning with highest match score for detected topic
                    selected_meaning = self.find_best_meaning_for_topic(meanings, topic_result)
                    
                except Exception as e:
                    self.logger.error(f"Error in AI topic detection: {str(e)}")
                    # Fall back to highest match score
                    selected_meaning = max(meanings, key=lambda m: m.match_score)
            else:
                # Without question, use highest match score
                selected_meaning = max(meanings, key=lambda m: m.match_score)
                
            if not selected_meaning:
                # If no meaning was selected, use the one with highest match score
                selected_meaning = max(meanings, key=lambda m: m.match_score)
            
            # Get base and position information for additional context
            base_names = ['วัน', 'เดือน', 'ปี', 'ผลรวม']
            position_names = {
                1: ['อัตตะ', 'หินะ', 'ธานัง', 'ปิตา', 'มาตา', 'โภคา', 'มัชฌิมา'],
                2: ['ตะนุ', 'กดุมภะ', 'สหัชชะ', 'พันธุ', 'ปุตตะ', 'อริ', 'ปัตนิ'],
                3: ['มรณะ', 'สุภะ', 'กัมมะ', 'ลาภะ', 'พยายะ', 'ทาสา', 'ทาสี']
            }
            
            base_name = base_names[selected_meaning.base - 1] if 0 < selected_meaning.base <= 4 else f"ฐาน {selected_meaning.base}"
            position_name = ""
            if selected_meaning.base <= 3 and 0 < selected_meaning.position <= 7:
                position_name = position_names[selected_meaning.base][selected_meaning.position - 1]
            
            # For debugging - log what we selected from DB
            self.logger.info(f"Selected meaning - Base: {base_name}, Position: {position_name}, Value: {selected_meaning.value}")
            self.logger.info(f"Selected meaning - Heading: {selected_meaning.heading}")
            self.logger.info(f"Selected meaning - Category: {selected_meaning.category}")
            
            # First try to generate a reading with external API
            personalized_reading = await self._generate_ai_reading(
                calculator_result=calculator_result,
                birth_date=birth_date,
                thai_day=thai_day or calculator_result.thai_day,
                user_question=user_question,
                selected_meaning=selected_meaning,
                topic=detected_topic,
                topic_result=topic_result
            )
            
            # If external API generation failed, try with local enhanced reading
            if not personalized_reading:
                self.logger.info("External API reading failed, trying local enhanced reading")
                personalized_reading = self._generate_enhanced_reading(
                    birth_date=birth_date,
                    thai_day=thai_day or calculator_result.thai_day,
                    user_question=user_question,
                    selected_meaning=selected_meaning,
                    topic=detected_topic,
                    topic_result=topic_result,
                    base_name=base_name,
                    position_name=position_name
                )
            
            # If both methods failed, fall back to the database reading
            if not personalized_reading:
                self.logger.info("Both reading generation methods failed, using raw database content")
                # Add context to heading if not already present
                enhanced_heading = selected_meaning.heading
                if position_name and position_name not in enhanced_heading:
                    enhanced_heading = f"{enhanced_heading} ({position_name})"
                
                return FortuneReading(
                    heading=enhanced_heading,
                    meaning=selected_meaning.meaning,
                    influence_type=selected_meaning.category,
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day or calculator_result.thai_day,
                    question=user_question
                )
            else:
                # Return the generated personalized reading
                return personalized_reading
            
        except Exception as e:
            self.logger.error(f"Error getting fortune reading: {str(e)}", exc_info=True)
            return FortuneReading(
                heading="เกิดข้อผิดพลาด",
                meaning="ขออภัย เกิดข้อผิดพลาดในการทำนาย",
                influence_type="ทั่วไป",
                birth_date="",
                thai_day=""
            )
            
    async def _generate_ai_reading(
        self,
        calculator_result: BasesResult,
        birth_date: datetime,
        thai_day: str,
        user_question: Optional[str],
        selected_meaning: Meaning,
        topic: str,
        topic_result: Optional[Dict[str, Any]] = None
    ) -> Optional[FortuneReading]:
        """
        Generate a personalized reading using AI instead of raw database content
        
        This creates a more user-friendly, coherent reading that integrates:
        1. The base and position values
        2. The detected topic
        3. The user's question
        4. Knowledge from the selected database reading
        
        Returns a FortuneReading object or None if generation fails
        """
        self.logger.info("Attempting to generate AI reading...")
        
        try:
            from app.services.openai_service import get_openai_service
            from app.services.prompt import PromptService
            from app.domain.birth import BirthInfo
            from app.config.settings import get_settings
            
            # Check if AI readings are enabled in settings
            settings = get_settings()
            if not settings.enable_ai_readings:
                self.logger.info("AI readings are disabled in settings, skipping")
                return None
                
            # Get services
            openai_service = await get_openai_service()
            
            # Check if OpenAI API is available
            if not await openai_service.is_available():
                self.logger.warning("OpenAI API is not available, falling back to database reading")
                return None
                
            prompt_service = PromptService()
            self.logger.debug("Services initialized for AI reading generation")
            
            # Get month from birth date
            month = birth_date.month
            
            # Get day value from Thai day
            day_value_map = {
                "อาทิตย์": 1, "จันทร์": 2, "อังคาร": 3, "พุธ": 4, 
                "พฤหัสบดี": 5, "ศุกร์": 6, "เสาร์": 7
            }
            day_value = day_value_map.get(thai_day, 4)  # Default to Wednesday (4) if not found
            
            # Calculate year start number (just use birth year % 10 as a simple approximation)
            year_start_number = birth_date.year % 10
            
            # Create birth info object for prompt generation
            birth_info = BirthInfo(
                date=birth_date,
                day=thai_day,
                day_value=day_value,
                month=month,
                year_animal=self._get_year_animal(birth_date.year),
                year_start_number=year_start_number
            )
            
            self.logger.debug(f"Created BirthInfo for {birth_date.strftime('%Y-%m-%d')}, {thai_day}")
            
            # Generate topic-specific heading
            topic_headings = {
                'การเงิน': "คำทำนายเรื่องการเงินและทรัพย์สิน",
                'ความรัก': "คำทำนายเรื่องความรักและความสัมพันธ์",
                'สุขภาพ': "คำทำนายเรื่องสุขภาพและความเป็นอยู่",
                'การงาน': "คำทำนายเรื่องการงานและอาชีพ",
                'การศึกษา': "คำทำนายเรื่องการศึกษาและการเรียนรู้",
                'ครอบครัว': "คำทำนายเรื่องครอบครัวและบ้าน",
                'โชคลาภ': "คำทำนายเรื่องโชคลาภและความสำเร็จ",
                'อนาคต': "คำทำนายเรื่องอนาคตและชะตาชีวิต",
                'การเดินทาง': "คำทำนายเรื่องการเดินทางและการย้ายถิ่น"
            }
            
            # Get heading based on topic
            heading = topic_headings.get(topic, f"คำทำนายเรื่อง{topic}")
            
            # Add confidence indication to heading if available
            if topic_result and topic_result.get('confidence', 0) > 7:
                heading += " (แม่นยำสูง)"
            
            # Create meanings collection for prompt service
            meanings_collection = MeaningCollection(items=[selected_meaning])
            
            self.logger.debug(f"Generating AI reading for topic: {topic}")
                
            # Generate user prompt
            user_prompt = prompt_service.generate_user_prompt(
                birth_info=birth_info,
                bases=calculator_result.bases,
                meanings=meanings_collection,
                question=user_question or "ขอคำทำนายทั่วไป",
                language="thai",  # Default to Thai
                topic=topic
            )
            
            # Generate system prompt for fortune telling
            system_prompt = prompt_service.generate_system_prompt(language="thai")
            
            self.logger.info(f"Calling OpenAI API for topic: {topic}")
            
            # Call OpenAI to generate personalized reading
            ai_response = await openai_service.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=settings.ai_reading_max_tokens,
                temperature=settings.ai_reading_temperature
            )
            
            # If AI generation is successful, return formatted FortuneReading
            if ai_response:
                # Clean up AI response
                meaning = ai_response.strip()
                
                # Determine influence type based on content analysis or from topic
                influence_type = self._determine_influence_type(meaning, topic, selected_meaning.category)
                
                self.logger.info(f"Successfully generated AI reading for topic: {topic}")
                
                return FortuneReading(
                    heading=heading,
                    meaning=meaning,
                    influence_type=influence_type,
                    birth_date=birth_date.strftime("%Y-%m-%d"),
                    thai_day=thai_day,
                    question=user_question
                )
            else:
                self.logger.warning("OpenAI API returned empty response, falling back to database reading")
            
            # Return None if generation fails
            return None
            
        except ImportError as e:
            self.logger.error(f"Import error in _generate_ai_reading: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"Error generating AI reading: {str(e)}", exc_info=True)
            return None
    
    def _get_year_animal(self, year: int) -> str:
        """Get Thai zodiac animal for a given year"""
        animals = [
            "ชวด (หนู)", "ฉลู (วัว)", "ขาล (เสือ)", "เถาะ (กระต่าย)", 
            "มะโรง (งูใหญ่)", "มะเส็ง (งูเล็ก)", "มะเมีย (ม้า)", "มะแม (แพะ)", 
            "วอก (ลิง)", "ระกา (ไก่)", "จอ (หมา)", "กุน (หมู)"
        ]
        return animals[(year - 4) % 12]
    
    def _determine_influence_type(
        self,
        meaning: str,
        topic: str,
        original_category: str
    ) -> str:
        """
        Determine the influence type based on the reading content and topic
        
        Args:
            meaning: The reading content
            topic: The detected topic
            original_category: The original category from the database
            
        Returns:
            str: The determined influence type
        """
        try:
            # First try to use the topic as influence type
            if topic in ['การเงิน', 'ความรัก', 'สุขภาพ', 'การงาน', 'การศึกษา', 'ครอบครัว', 'โชคลาภ', 'อนาคต', 'การเดินทาง']:
                return topic
                
            # If topic is not a standard influence type, analyze the content
            positive_keywords = ['ดี', 'เจริญ', 'รุ่งเรือง', 'สำเร็จ', 'โชคลาภ', 'มั่งมี', 'สมหวัง', 'สุข']
            negative_keywords = ['ไม่ดี', 'ระวัง', 'อันตราย', 'เสีย', 'ยาก', 'ลำบาก', 'ทุกข์']
            
            positive_count = sum(1 for word in positive_keywords if word in meaning)
            negative_count = sum(1 for word in negative_keywords if word in meaning)
            
            if positive_count > negative_count:
                return 'ดี'
            elif negative_count > positive_count:
                return 'ไม่ดี'
            else:
                # If counts are equal or no keywords found, use original category
                return original_category
                
        except Exception as e:
            self.logger.error(f"Error determining influence type: {str(e)}")
            return original_category
    
    def _filter_and_rank_meanings(self, meanings: List[Meaning], user_question: Optional[str] = None) -> List[Meaning]:
        """
        Filter and rank meanings to provide more relevant results
        
        This helps when we have a large number of meanings (like 2000+) by:
        1. Filtering out obviously irrelevant meanings 
        2. Boosting scores for more relevant meanings based on content and context
        """
        if not meanings:
            return []
            
        # If no question, just return all meanings
        if not user_question:
            return meanings
            
        filtered_meanings = []
        user_question_lower = user_question.lower()
        
        # Keywords indicating question importance/urgency
        importance_keywords = [
            'จำเป็น', 'สำคัญ', 'เร่งด่วน', 'กังวล', 'กลุ้มใจ', 'ไม่สบายใจ', 
            'ต้องการคำแนะนำ', 'ช่วยแนะนำ', 'แนะนำ', 'ทำอย่างไร', 'ทำอย่างไรดี'
        ]
        
        question_has_importance = any(kw in user_question_lower for kw in importance_keywords)
        
        # Get all bases' values for priority filtering
        base_values = {1: set(), 2: set(), 3: set(), 4: set()}
        for m in meanings:
            if 1 <= m.base <= 4:
                base_values[m.base].add(m.value)
        
        # Define priority values (1, 5, 7 are often significant in Thai numerology)
        priority_values = {1, 5, 7}
        
        for meaning in meanings:
            # Start with original match score
            adjusted_score = meaning.match_score
            
            # 1. Check for meaning content relevance
            meaning_content = (meaning.meaning or "").lower()
            
            # Prioritize meanings with significant values
            if meaning.value in priority_values:
                adjusted_score *= 1.2
            
            # 2. Prioritize meanings from base 1 (Day) and base 4 (Sum) 
            # which are often more significant in Thai astrology
            if meaning.base == 1:  # Day base (personal)
                adjusted_score *= 1.3
            elif meaning.base == 4:  # Sum base (overview)
                adjusted_score *= 1.2
            
            # 3. Prioritize center positions which are often more significant
            if 3 <= meaning.position <= 5:
                adjusted_score *= 1.1
                
            # 4. If question has urgency keywords, prioritize interpretations that have 
            # concrete advice/guidance
            if question_has_importance:
                advice_indicators = ['ควร', 'แนะนำ', 'ช่วย', 'ทำ', 'อย่า', 'ระวัง', 'พยายาม']
                if any(ind in meaning_content for ind in advice_indicators):
                    adjusted_score *= 1.4
            
            # 5. Ensure adequate but not overwhelming amount of content
            content_length = len(meaning_content)
            if 100 <= content_length <= 500:  # Ideal length
                adjusted_score *= 1.1
            elif content_length > 500:  # Comprehensive reading
                adjusted_score *= 1.05
            elif content_length < 50:  # Too short
                adjusted_score *= 0.8
            
            # Update the score and add to filtered list
            meaning.match_score = adjusted_score
            filtered_meanings.append(meaning)
            
        # Sort by adjusted score and return top results
        filtered_meanings.sort(key=lambda m: m.match_score, reverse=True)
        
        # Return either all meanings or top 200, whichever is smaller
        # This limits the processing for the find_best_meaning_for_topic method
        return filtered_meanings[:200] if len(filtered_meanings) > 200 else filtered_meanings

    def find_best_meaning_for_topic(self, meanings: List[Meaning], topic_result: Dict[str, Any]) -> Optional[Meaning]:
        """Find the best meaning for a detected topic"""
        try:
            primary_topic = topic_result['primary_topic']
            self.logger.debug(f"Finding meanings for topic: {primary_topic}")
            
            # Define related categories for each topic to improve matching
            topic_related_categories = {
                'การเงิน': ['หินะ', 'ทรัพย์', 'เงิน', 'ธุรกิจ', 'กดุมภะ', 'ลาภะ'],
                'ความรัก': ['มาตา', 'คู่ครอง', 'ความรัก', 'ปุตตะ', 'ปัตนิ'],
                'สุขภาพ': ['โภคา', 'อัตตะ', 'ร่างกาย', 'สุขภาพ', 'ตะนุ'],
                'การงาน': ['โภคา', 'กัมมะ', 'อาชีพ', 'หน้าที่', 'งาน'],
                'การศึกษา': ['ธานัง', 'การเรียนรู้', 'วิชาการ', 'สหัชชะ'],
                'ครอบครัว': ['ปิตา', 'มาตา', 'บ้าน', 'ครอบครัว', 'พันธุ'],
                'โชคลาภ': ['ลาภะ', 'โชค', 'หินะ', 'ทรัพย์', 'สุภะ'],
                'อนาคต': ['พยายะ', 'อนาคต', 'แนวโน้ม', 'ทิศทาง'],
                'การเดินทาง': ['ธานัง', 'สหัชชะ', 'เดินทาง', 'ย้ายถิ่น']
            }
            
            # Get related categories for our topic
            related_categories = topic_related_categories.get(primary_topic, [])
            related_categories.append(primary_topic)  # Include the topic itself
            
            # Add secondary topics related categories
            for secondary_topic in topic_result.get('secondary_topics', []):
                if secondary_topic in topic_related_categories:
                    related_categories.extend(topic_related_categories[secondary_topic])
            
            # Remove duplicates while preserving order
            seen = set()
            related_categories = [x for x in related_categories if not (x in seen or seen.add(x))]
            
            self.logger.debug(f"Related categories: {related_categories}")
            
            # Find meanings matching any related category (weighted scoring)
            matching_meanings = []
            for meaning in meanings:
                category = meaning.category or ""
                # Calculate match score based on how many related categories appear in the meaning
                match_weight = 0
                for i, related in enumerate(related_categories):
                    # Earlier items in related_categories have higher priority
                    if related.lower() in category.lower():
                        # Exponential decay of importance (first items worth more)
                        match_weight += 1.0 / (i + 1)
                
                if match_weight > 0:
                    # Adjust the match score based on the weight and AI confidence
                    confidence_factor = topic_result['confidence'] / 10.0
                    adjusted_score = meaning.match_score * (1 + match_weight) * confidence_factor
                    
                    # Store original score temporarily
                    original_score = meaning.match_score
                    meaning.match_score = adjusted_score
                    
                    matching_meanings.append((meaning, original_score))
            
            # If we found matches, select the one with highest adjusted match score
            if matching_meanings:
                matching_meanings.sort(key=lambda x: x[0].match_score, reverse=True)
                selected_meaning, original_score = matching_meanings[0]
                
                self.logger.info(f"Selected meaning with topic: {primary_topic}, score: {selected_meaning.match_score:.2f}")
                self.logger.info(f"Selected meaning category: {selected_meaning.category}")
                
                # Restore original score after sorting
                selected_meaning.match_score = original_score
                return selected_meaning
            
            # FALLBACK: If no matches found with related categories, use base match score
            self.logger.warning(f"No meanings found matching topic {primary_topic} or related categories")
            
            # Sort all meanings by match score and return the best one
            best_meaning = max(meanings, key=lambda m: m.match_score)
            self.logger.info(f"Using best available meaning with score {best_meaning.match_score:.2f}")
            return best_meaning
            
        except Exception as e:
            self.logger.error(f"Error finding best meaning for topic: {str(e)}", exc_info=True)
            return None

    def _generate_enhanced_reading(
        self,
        birth_date: datetime,
        thai_day: str,
        user_question: Optional[str],
        selected_meaning: Meaning,
        topic: str,
        topic_result: Optional[Dict[str, Any]] = None,
        base_name: str = "",
        position_name: str = ""
    ) -> Optional[FortuneReading]:
        """
        Generate an enhanced reading without external API calls
        
        This method creates a more user-friendly reading by:
        1. Using a clear topic-specific heading
        2. Adding context about which base/position is relevant
        3. Structuring the content in readable paragraphs
        4. Adding topic-specific insights
        """
        try:
            self.logger.info(f"Generating local enhanced reading for topic: {topic}")
            
            # Generate topic-specific heading
            topic_headings = {
                'การเงิน': "คำทำนายเรื่องการเงินและทรัพย์สิน",
                'ความรัก': "คำทำนายเรื่องความรักและความสัมพันธ์",
                'สุขภาพ': "คำทำนายเรื่องสุขภาพและความเป็นอยู่",
                'การงาน': "คำทำนายเรื่องการงานและอาชีพ",
                'การศึกษา': "คำทำนายเรื่องการศึกษาและการเรียนรู้",
                'ครอบครัว': "คำทำนายเรื่องครอบครัวและบ้าน",
                'โชคลาภ': "คำทำนายเรื่องโชคลาภและความสำเร็จ",
                'อนาคต': "คำทำนายเรื่องอนาคตและชะตาชีวิต",
                'การเดินทาง': "คำทำนายเรื่องการเดินทางและการย้ายถิ่น"
            }
            
            # Get heading based on topic
            heading = topic_headings.get(topic, f"คำทำนายเรื่อง{topic}")
            
            # Add confidence indication to heading if available
            if topic_result and topic_result.get('confidence', 0) > 7:
                heading += " (แม่นยำสูง)"
                
            # Get the raw meaning content
            raw_meaning = selected_meaning.meaning
            
            # Structure the meaning into paragraphs if it's not already
            paragraphs = raw_meaning.split("\n")
            if len(paragraphs) <= 1:
                # If the meaning is just one paragraph, try to split by periods
                parts = raw_meaning.split(". ")
                if len(parts) > 1:
                    # Group parts into approximately 2-3 sentences per paragraph
                    group_size = max(1, len(parts) // 3)
                    new_paragraphs = []
                    for i in range(0, len(parts), group_size):
                        group = parts[i:i+group_size]
                        # Add period back to the end of sentences except the last part
                        for j in range(len(group) - 1):
                            group[j] += "."
                        # Last part might already have a period
                        if not group[-1].endswith("."):
                            group[-1] += "."
                        new_paragraphs.append(" ".join(group))
                    paragraphs = new_paragraphs
            
            # Create introduction paragraph
            intro = f"จากการคำนวณฐาน{base_name} ตำแหน่ง{position_name} ของคุณ ทำนายได้ว่า:\n\n"
            
            # Add contextual paragraph at the end based on the topic
            topic_context = {
                'การเงิน': "ในด้านการเงิน คุณควรระมัดระวังการใช้จ่ายและวางแผนการเงินอย่างรอบคอบในช่วงนี้ การลงทุนควรพิจารณาอย่างรอบด้านและไม่ประมาท",
                'ความรัก': "สำหรับความรัก การสื่อสารอย่างเปิดใจจะช่วยเสริมสร้างความเข้าใจและความสัมพันธ์ที่ดี ให้ความสำคัญกับความรู้สึกของคนรอบข้าง",
                'สุขภาพ': "ด้านสุขภาพ ควรดูแลตัวเองอย่างสม่ำเสมอ ออกกำลังกายพอประมาณและพักผ่อนให้เพียงพอ หลีกเลี่ยงความเครียดสะสม",
                'การงาน': "ในเรื่องการงาน ความขยันและความอดทนจะนำไปสู่ความสำเร็จ อย่ากลัวที่จะเรียนรู้สิ่งใหม่ๆและพัฒนาทักษะของตัวเอง",
                'การศึกษา': "สำหรับการศึกษา ควรตั้งใจเรียนและแบ่งเวลาอย่างมีประสิทธิภาพ การทบทวนบทเรียนอย่างสม่ำเสมอจะช่วยให้เข้าใจเนื้อหาได้ดียิ่งขึ้น",
                'ครอบครัว': "ในด้านครอบครัว ควรให้เวลากับคนในครอบครัวและรับฟังความคิดเห็นของทุกคน ความเข้าใจและการให้อภัยจะช่วยรักษาความสัมพันธ์ที่ดี",
                'โชคลาภ': "สำหรับโชคลาภ โอกาสดีๆ อาจเข้ามาโดยไม่คาดคิด แต่อย่าหวังพึ่งโชคชะตาเพียงอย่างเดียว ความพยายามและความขยันเป็นสิ่งสำคัญ",
                'อนาคต': "สำหรับอนาคต การวางแผนและเตรียมพร้อมรับมือกับการเปลี่ยนแปลงจะช่วยให้คุณก้าวไปข้างหน้าได้อย่างมั่นคง",
                'การเดินทาง': "ในเรื่องการเดินทาง ควรวางแผนและเตรียมตัวให้พร้อม ศึกษาข้อมูลเส้นทางและสถานที่ให้ละเอียดเพื่อความปลอดภัยและความราบรื่น"
            }
            
            conclusion = f"\n\n{topic_context.get(topic, 'ขอให้คุณพบเจอแต่สิ่งดีๆ และมีความสุขในชีวิต')}"
            
            # Build the complete meaning
            meaning = intro + "\n".join(paragraphs) + conclusion
            
            # Determine influence type
            influence_type = self._determine_influence_type(meaning, topic, selected_meaning.category)
            
            self.logger.info(f"Successfully generated enhanced local reading for topic: {topic}")
            
            return FortuneReading(
                heading=heading,
                meaning=meaning,
                influence_type=influence_type,
                birth_date=birth_date.strftime("%Y-%m-%d"),
                thai_day=thai_day,
                question=user_question
            )
        except Exception as e:
            self.logger.error(f"Error generating enhanced reading: {str(e)}", exc_info=True)
            return None


# Factory function for dependency injection
async def get_reading_service(
    reading_repository: ReadingRepository = Depends(),
    category_repository: CategoryRepository = Depends()
) -> ReadingService:
    """Get reading service instance when called from code or through dependency injection"""
    # For direct calls outside of FastAPI's dependency injection system,
    # we need to create new repository instances
    try:
        # If this is called directly (not through FastAPI's DI system)
        # Just create new repositories directly
        from app.repository.reading_repository import get_reading_repository
        from app.repository.category_repository import get_category_repository
        
        # Always create new repositories when called directly
        direct_reading_repo = get_reading_repository()
        direct_category_repo = get_category_repository()
        
        return ReadingService(direct_reading_repo, direct_category_repo)
    except Exception as e:
        # Log the error but don't crash
        import logging
        logging.error(f"Error in get_reading_service: {str(e)}")
        
        # Create repositories directly as a last resort
        from app.domain.meaning import Reading, Category
        from app.repository.reading_repository import ReadingRepository
        from app.repository.category_repository import CategoryRepository
        
        reading_repo = ReadingRepository(Reading)
        category_repo = CategoryRepository(Category)
        
        return ReadingService(reading_repo, category_repo)