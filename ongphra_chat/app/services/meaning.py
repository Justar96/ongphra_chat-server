# app/services/meaning.py
from typing import Dict, List, Set, Optional, Any
import re
import json
from datetime import datetime

from openai import AsyncOpenAI
from app.domain.bases import Bases, BasesResult
from app.domain.meaning import Meaning, MeaningCollection, Category, Reading
from app.repository.category_repository import CategoryRepository
from app.repository.reading_repository import ReadingRepository
from app.core.exceptions import MeaningExtractionError
from app.core.logging import get_logger
from app.config.settings import get_settings


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
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Initialized MeaningService")
        
        # Initialize Thai position labels from calculator
        try:
            from app.services.calculator import CalculatorService
            calculator = CalculatorService()
            self.day_labels = calculator.day_labels
            self.month_labels = calculator.month_labels
            self.year_labels = calculator.year_labels
            self.logger.debug(f"Initialized Thai position labels from calculator: " +
                             f"day={self.day_labels}, month={self.month_labels}, year={self.year_labels}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize labels from calculator: {str(e)}. Using defaults.")
            # Fallback to default labels if calculator import fails
            self.day_labels = ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
            self.month_labels = ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"],
            self.year_labels = ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]
        
        # Initialize category mappings for house numbers and meanings
        self.CATEGORY_MAPPINGS = {
            'กดุมภะ': {'thai_meaning': 'รายได้รายจ่าย', 'house_number': 1, 'house_type': 'กาลปักษ์'},
            'กัมมะ': {'thai_meaning': 'หน้าที่การงาน', 'house_number': 2, 'house_type': 'เกณฑ์ชะตา'},
            'ตะนุ': {'thai_meaning': 'ตัวท่านเอง', 'house_number': 3, 'house_type': 'จร'},
            'ทาสา': {'thai_meaning': 'เหน็จเหนื่อยเพื่อคนอื่น ส่วนรวม', 'house_number': 4, 'house_type': 'กาลปักษ์'},
            'ทาสี': {'thai_meaning': 'การเหน็จเหนื่อยเพื่อตัวเอง', 'house_number': 5, 'house_type': 'เกณฑ์ชะตา'},
            'ธานัง': {'thai_meaning': 'เรื่องเงิน ๆ ทอง ๆ', 'house_number': 6, 'house_type': 'จร'},
            'ปัตนิ': {'thai_meaning': 'คู่ครอง', 'house_number': 7, 'house_type': 'กาลปักษ์'},
            'ปิตา': {'thai_meaning': 'พ่อหรือผู้ใหญ่ เรื่องนอกบ้าน', 'house_number': 8, 'house_type': 'เกณฑ์ชะตา'},
            'ปุตตะ': {'thai_meaning': 'เรื่องลูก การเริ่มต้น', 'house_number': 9, 'house_type': 'จร'},
            'พยายะ': {'thai_meaning': 'สิ่งไม่ดี เรื่องปิดบัง ซ่อนเร้น', 'house_number': 10, 'house_type': 'กาลปักษ์'},
            'พันธุ': {'thai_meaning': 'ญาติพี่น้อง', 'house_number': 11, 'house_type': 'เกณฑ์ชะตา'},
            'มรณะ': {'thai_meaning': 'เรื่องเจ็บป่วย', 'house_number': 12, 'house_type': 'กาลปักษ์'},
            'มัชฌิมา': {'thai_meaning': 'เรื่องกลาง ๆ ไม่หนักหนา', 'house_number': 1, 'house_type': 'กาลปักษ์'},
            'มาตา': {'thai_meaning': 'แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว', 'house_number': 2, 'house_type': 'เกณฑ์ชะตา'},
            'ลาภะ': {'thai_meaning': 'ลาภยศ โชคลาภ', 'house_number': 3, 'house_type': 'จร'},
            'สหัชชะ': {'thai_meaning': 'เพื่อนฝูง การติดต่อ', 'house_number': 4, 'house_type': 'กาลปักษ์'},
            'สุภะ': {'thai_meaning': 'ความเจริญรุ่งเรือง', 'house_number': 5, 'house_type': 'เกณฑ์ชะตา'},
            'หินะ': {'thai_meaning': 'ความผิดหวัง', 'house_number': 6, 'house_type': 'กาลปักษ์'},
            'อริ': {'thai_meaning': 'ปัญหา อุปสรรค', 'house_number': 7, 'house_type': 'กาลปักษ์'},
            'อัตตะ': {'thai_meaning': 'ตัวท่านเอง', 'house_number': 8, 'house_type': 'กาลปักษ์'},
            'โภคา': {'thai_meaning': 'สินทรัพย์', 'house_number': 9, 'house_type': 'จร'},
        }
        self.logger.debug(f"Initialized category mappings with {len(self.CATEGORY_MAPPINGS)} categories")
        
        # Initialize OpenAI client
        settings = get_settings()
        self.openai_api_key = settings.openai_api_key
        self.default_model = settings.default_model
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        self.logger.debug(f"Initialized OpenAI client with model {self.default_model}")
        
        # Initialize meaning cache
        self._meaning_cache = {}
        # Initialize topic identification cache
        self._topic_cache = {}
    
    async def identify_topics(self, question: str) -> Set[str]:
        """Identify relevant topics based on the question"""
        if not question: 
            # Default to work and fortune pair
            return {"กัมมะ:ลาภะ"}
            
        self.logger.debug(f"Identifying topics for question: '{question}'")
        
        # Check cache first
        if question in self._topic_cache:
            topics = self._topic_cache[question]
            self.logger.debug(f"Using cached topics for question: {topics}")
            return topics
        
        # Use AI-based topic identification
        try:
            ai_topics = await self._identify_topics_with_ai(question)
            topics = set(ai_topics)
            self.logger.debug(f"Identified topics with AI: {topics}")
        except Exception as e:
            # Default to work and fortune pair if AI identification fails
            self.logger.error(f"AI topic identification failed: {str(e)}")
            topics = {"กัมมะ:ลาภะ"}
            self.logger.debug("Using default topics due to AI failure")
        
        # Cache the result
        self._topic_cache[question] = topics
        
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
        """Generate a cache key for the given bases and question"""
        # Use a simple hash of the bases and question
        base_str = f"{bases.base1}-{bases.base2}-{bases.base3}-{bases.base4}"
        return f"{base_str}:{question}"
    
    def _get_cached_meaning(self, cache_key: str) -> Optional[MeaningCollection]:
        """Get cached meaning if available"""
        if cache_key in self._meaning_cache:
            return self._meaning_cache[cache_key]
        return None
    
    def _cache_meaning(self, cache_key: str, meaning: MeaningCollection) -> None:
        """Cache the meaning result"""
        # Store in cache - only keep up to 100 items
        if len(self._meaning_cache) >= 100:
            # Remove oldest item
            oldest_key = next(iter(self._meaning_cache))
            del self._meaning_cache[oldest_key]
            
        self._meaning_cache[cache_key] = meaning
    
    async def _identify_topics_with_ai(self, question: str) -> List[str]:
        """
        Identify topics from the question using AI
        
        Args:
            question: User's question
            
        Returns:
            List of identified topics (category pairs)
        """
        try:
            # Check cache first
            if question in self._topic_cache:
                return list(self._topic_cache[question])
            
            self.logger.info(f"Identifying topics with AI for question: '{question}'")
            
            # Thai position names from calculator.py
            thai_positions = {
                "day_labels": ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"],
                "month_labels": ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"],
                "year_labels": ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]
            }
            
            # Create a list of available categories with their meanings from CATEGORY_MAPPINGS
            categories_info = []
            for category_name, details in self.CATEGORY_MAPPINGS.items():
                # Only include categories that are in the Thai position names
                if category_name in thai_positions["day_labels"] or \
                   category_name in thai_positions["month_labels"] or \
                   category_name in thai_positions["year_labels"]:
                    categories_info.append({
                        "name": category_name,
                        "thai_meaning": details.get("thai_meaning", ""),
                        "house_number": details.get("house_number", 0),
                        "house_type": details.get("house_type", ""),
                        "base_type": "day_labels" if category_name in thai_positions["day_labels"] else 
                                    "month_labels" if category_name in thai_positions["month_labels"] else 
                                    "year_labels"
                    })
            
            # Create the system prompt - explicitly request exactly 3 pairs
            system_prompt = """
            คุณเป็นผู้เชี่ยวชาญในการวิเคราะห์คำถามเกี่ยวกับโหราศาสตร์ไทย
            งานของคุณคือการระบุคู่ของภพที่เกี่ยวข้องกับคำถามของผู้ใช้
            
            ให้วิเคราะห์คำถามและระบุ 3 คู่ของภพที่สัมพันธ์กันและเกี่ยวข้องกับคำถาม (ไม่มากกว่าหรือน้อยกว่า 3 คู่)
            ตอบในรูปแบบ JSON array ของคู่ภพ โดยในแต่ละคู่ประกอบด้วย primary_house และ secondary_house
            ถ้าไม่มีคู่ภพที่เกี่ยวข้องชัดเจน ให้เลือกภพที่น่าจะเกี่ยวข้องที่สุด 3 คู่
            
            เลือกภพตาม "thai_meaning" ที่ตรงกับเนื้อหาของคำถาม
            โดยควรเลือกภพหลัก (primary_house) จากประเภทหนึ่ง และภพรอง (secondary_house) จากอีกประเภทหนึ่ง
            เรียงลำดับคู่ภพจากมีความเกี่ยวข้องมากที่สุดไปน้อยที่สุด
            
            ตัวอย่างคำตอบ: 
            [
              {"primary_house": "กัมมะ", "secondary_house": "ลาภะ"},
              {"primary_house": "ธานัง", "secondary_house": "อัตตะ"},
              {"primary_house": "ลาภะ", "secondary_house": "กดุมภะ"}
            ]
            """
            
            # Create the user prompt
            user_prompt = f"""
            คำถามของผู้ใช้: {question}
            
            ภพที่มีให้เลือก:
            {json.dumps(categories_info, ensure_ascii=False, indent=2)}
            
            โปรดระบุ 3 คู่ของภพที่เกี่ยวข้องกับคำถามนี้ในรูปแบบ JSON array ของคู่ภพ
            โดยในแต่ละคู่ประกอบด้วย primary_house และ secondary_house
            เรียงลำดับจากคู่ที่เกี่ยวข้องมากที่สุดไปหาน้อยที่สุด
            
            คำตอบต้องมีทั้งหมด 3 คู่เท่านั้น ไม่มากกว่าหรือน้อยกว่า
            พยายามเลือกภพจากประเภทที่ต่างกัน เช่น หากเลือก primary_house จาก day_labels 
            ให้เลือก secondary_house จาก month_labels หรือ year_labels
            """
            
            # Create the messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Call the OpenAI API
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more deterministic results
                max_tokens=200
            )
            
            # Extract the response
            response_text = response.choices[0].message.content.strip()
            self.logger.debug(f"AI response for topic identification: {response_text}")
            
            # Parse the JSON response
            try:
                # Try to extract JSON from the response if it's not a clean JSON
                if not response_text.startswith('['):
                    match = re.search(r'\[(.*?)\]', response_text, re.DOTALL)
                    if match:
                        response_text = f"[{match.group(1)}]"
                
                house_pairs = json.loads(response_text)
                
                # Convert house pairs to topics list
                topics = []
                
                for pair in house_pairs:
                    primary_house = pair.get("primary_house")
                    secondary_house = pair.get("secondary_house")
                    
                    if primary_house and secondary_house:
                        if primary_house in self.CATEGORY_MAPPINGS and secondary_house in self.CATEGORY_MAPPINGS:
                            # Create a topic identifier that represents the pair
                            topics.append(f"{primary_house}:{secondary_house}")
                
                # Ensure we have exactly 3 pairs or use defaults if needed
                if not topics:
                    # Use default pairs
                    topics = ["กัมมะ:ลาภะ", "ธานัง:อัตตะ", "ลาภะ:กดุมภะ"]
                    self.logger.warning("No valid topics from AI, using default 3 pairs")
                elif len(topics) < 3:
                    # Add default pairs to reach 3
                    defaults = ["กัมมะ:ลาภะ", "ธานัง:อัตตะ", "ลาภะ:กดุมภะ"]
                    for default_topic in defaults:
                        if default_topic not in topics and len(topics) < 3:
                            topics.append(default_topic)
                    self.logger.warning(f"Only {len(topics)} valid topics from AI, adding defaults to reach 3")
                elif len(topics) > 3:
                    # Limit to 3 most relevant pairs
                    topics = topics[:3]
                    self.logger.warning(f"Too many topics from AI, limiting to 3 most relevant")
                
                # Cache the result
                self._topic_cache[question] = set(topics)
                
                return topics
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse AI response as JSON: {response_text}")
                # Use 3 default pairs
                default_topics = ["กัมมะ:ลาภะ", "ธานัง:อัตตะ", "ลาภะ:กดุมภะ"]
                self._topic_cache[question] = set(default_topics)
                return default_topics
                
        except Exception as e:
            self.logger.error(f"Error identifying topics with AI: {str(e)}", exc_info=True)
            # Use 3 default pairs
            default_topics = ["กัมมะ:ลาภะ", "ธานัง:อัตตะ", "ลาภะ:กดุมภะ"]
            self._topic_cache[question] = set(default_topics)
            return default_topics
    
    async def extract_meanings(self, bases: Bases, question: str) -> MeaningCollection:
        """
        Extract meanings from bases based on the question
        
        Args:
            bases: Calculated bases
            question: User's question
            
        Returns:
            Collection of meanings
        """
        try:
            self.logger.info(f"Extracting meanings for question: '{question}'")
            
            # Generate cache key
            cache_key = self._get_cache_key(bases, question)
            
            # Check cache first
            cached_result = self._get_cached_meaning(cache_key)
            if cached_result:
                self.logger.info(f"Using cached meanings for question: '{question}'")
                return cached_result
            
            # Identify topics from the question using AI - now returns exactly 3 pairs
            topics = await self._identify_topics_with_ai(question)
            self.logger.info(f"Identified topics with AI: {', '.join(topics)}")
            
            # Parse topics to find specific combinations - process each pair separately
            all_specific_combinations = []
            regular_category_ids = []
            
            # Track combinations by pair to ensure equal representation
            pair_combinations = {}
            
            for topic in topics:
                # Check if this is a paired topic
                if ":" in topic:
                    primary_house, secondary_house = topic.split(":", 1)
                    
                    # Get the primary and secondary categories
                    primary_category = await self.category_repository.get_by_name(primary_house)
                    secondary_category = await self.category_repository.get_by_name(secondary_house)
                    
                    if primary_category and secondary_category:
                        # Get specific combinations for this pair
                        combinations = await self.category_repository.get_combinations_by_categories(
                            primary_category.id, secondary_category.id
                        )
                        
                        if combinations:
                            # Limit to at most 2 combinations per pair
                            limited_combinations = combinations[:2]
                            pair_combinations[topic] = limited_combinations
                            self.logger.debug(f"Found {len(combinations)} specific combinations for {topic}, using {len(limited_combinations)}")
                            all_specific_combinations.extend(limited_combinations)
                        else:
                            # If no direct combinations, add the individual categories
                            self.logger.debug(f"No specific combinations found for {topic}, adding individual categories")
                            regular_category_ids.append(primary_category.id)
                            regular_category_ids.append(secondary_category.id)
                else:
                    # Regular single category topic
                    categories = await self._get_categories_for_topic(topic)
                    if categories:
                        regular_category_ids.extend([cat.id for cat in categories])
            
            # Get readings for specific combinations
            meanings = []
            if all_specific_combinations:
                self.logger.info(f"Querying readings for {len(all_specific_combinations)} specific combinations (max 2 per pair)")
                
                # Extract combination IDs
                combination_ids = [comb['id'] for comb in all_specific_combinations]
                
                # Get readings for these specific combinations
                specific_readings = await self.reading_repository.get_by_combinations(combination_ids)
                self.logger.info(f"Found {len(specific_readings)} relevant readings from specific combinations")
                
                # Convert specific readings to meanings
                for reading in specific_readings:
                    try:
                        # Get the combination to determine which bases and positions to use
                        combination = next((c for c in all_specific_combinations if c['id'] == reading.combination_id), None)
                        
                        if combination:
                            # Handle both dictionary and object access patterns
                            category1_id = combination.get('category1_id')
                            category2_id = combination.get('category2_id')
                            category3_id = combination.get('category3_id', None)
                            
                            if not category1_id or not category2_id:
                                self.logger.warning(f"Invalid combination data: {combination}")
                                continue
                            
                            # Get the categories in this combination
                            cat1 = await self.category_repository.get_by_id(category1_id)
                            cat2 = await self.category_repository.get_by_id(category2_id)
                            cat3 = None
                            if category3_id:
                                cat3 = await self.category_repository.get_by_id(category3_id)
                            
                            # Determine base and position from categories
                            if cat1 and cat2:
                                base = self._get_base_for_house_number(cat1.house_number)
                                position = self._get_position_for_house_number(cat2.house_number)
                                
                                # Get the value from the corresponding base
                                base_keys = ["base1", "base2", "base3", "base4"]
                                if 1 <= base <= 4 and 1 <= position <= 7:
                                    base_key = base_keys[base - 1]
                                    base_sequence = getattr(bases, base_key)
                                    value = base_sequence[position - 1] if position <= len(base_sequence) else 0
                                    
                                    # Create meaning with higher match score for specific combinations
                                    meaning = Meaning(
                                        base=base,
                                        position=position,
                                        value=value,
                                        heading=reading.heading,
                                        meaning=reading.meaning,
                                        category=f"{cat1.name}-{cat2.name}" + (f"-{cat3.name}" if cat3 else ""),
                                        match_score=9.0  # Higher match score for specific combinations
                                    )
                                    meanings.append(meaning)
                    except Exception as inner_e:
                        # Log the error but continue processing other readings
                        self.logger.error(f"Error processing specific reading {reading.id if hasattr(reading, 'id') else 'unknown'}: {str(inner_e)}")
                        continue
            
            # If we have regular categories or not enough specific meanings, get regular readings too
            if regular_category_ids or len(meanings) < 5:
                # Limit regular category IDs to 6 to reduce database queries
                regular_category_ids = list(set(regular_category_ids))[:6]
                
                # Get regular readings by category IDs
                regular_readings = await self.reading_repository.get_by_categories(regular_category_ids)
                self.logger.info(f"Found {len(regular_readings)} relevant readings from regular categories")
                
                # Convert regular readings to meanings
                for reading in regular_readings:
                    try:
                        # Get the combination to determine which bases and positions to use
                        combination = await self.category_repository.get_combination_by_id(reading.combination_id)
                        if combination:
                            # Handle both dictionary and object access patterns
                            category1_id = combination.category1_id if hasattr(combination, 'category1_id') else combination.get('category1_id')
                            category2_id = combination.category2_id if hasattr(combination, 'category2_id') else combination.get('category2_id')
                            category3_id = combination.category3_id if hasattr(combination, 'category3_id') else combination.get('category3_id', None)
                            
                            if not category1_id or not category2_id:
                                self.logger.warning(f"Invalid combination data: {combination}")
                                continue
                            
                            # Get the categories in this combination
                            cat1 = await self.category_repository.get_by_id(category1_id)
                            cat2 = await self.category_repository.get_by_id(category2_id)
                            cat3 = None
                            if category3_id:
                                cat3 = await self.category_repository.get_by_id(category3_id)
                            
                            # Determine base and position from categories
                            if cat1 and cat2:
                                base = self._get_base_for_house_number(cat1.house_number)
                                position = self._get_position_for_house_number(cat2.house_number)
                                
                                # Get the value from the corresponding base
                                base_keys = ["base1", "base2", "base3", "base4"]
                                if 1 <= base <= 4 and 1 <= position <= 7:
                                    base_key = base_keys[base - 1]
                                    base_sequence = getattr(bases, base_key)
                                    value = base_sequence[position - 1] if position <= len(base_sequence) else 0
                                    
                                    # Create meaning
                                    meaning = Meaning(
                                        base=base,
                                        position=position,
                                        value=value,
                                        heading=reading.heading,
                                        meaning=reading.meaning,
                                        category=f"{cat1.name}-{cat2.name}" + (f"-{cat3.name}" if cat3 else ""),
                                        match_score=5.0  # Lower match score for regular category matches
                                    )
                                    meanings.append(meaning)
                    except Exception as inner_e:
                        # Log the error but continue processing other readings
                        self.logger.error(f"Error processing regular reading {reading.id if hasattr(reading, 'id') else 'unknown'}: {str(inner_e)}")
                        continue
            
            # Sort meanings by match score (highest first)
            meanings.sort(key=lambda m: getattr(m, 'match_score', 0), reverse=True)
            
            # Limit to a reasonable number of meanings
            if len(meanings) > 20:
                meanings = meanings[:20]
            
            # Create and return collection
            result = MeaningCollection(items=meanings)
            self.logger.info(f"Extracted {len(meanings)} meanings for question")
            
            # Cache the result
            self._cache_meaning(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting meanings: {str(e)}", exc_info=True)
            raise MeaningExtractionError(f"Error extracting meanings: {str(e)}")
    
    def _get_base_for_house_number(self, house_number: int) -> int:
        """Map house number to base (1-4)"""
        # Map house numbers to bases
        # Houses 1-3 -> Base 1
        # Houses 4-6 -> Base 2
        # Houses 7-9 -> Base 3
        # Houses 10-12 -> Base 4
        if 1 <= house_number <= 3:
            return 1
        elif 4 <= house_number <= 6:
            return 2
        elif 7 <= house_number <= 9:
            return 3
        elif 10 <= house_number <= 12:
            return 4
        else:
            return 1  # Default to base 1
    
    def _get_position_for_house_number(self, house_number: int) -> int:
        """Map house number to position (1-7)"""
        # Map house numbers to positions within a base
        # For each base, houses are mapped to positions 1-7
        # We use modulo to handle the mapping
        position = ((house_number - 1) % 12) % 7 + 1
        return position
    
    async def _get_categories_for_topic(self, topic: str) -> List[Category]:
        """
        Get categories related to a topic
        
        Args:
            topic: Topic identifier, either a single category name or a paired format like "primary:secondary"
            
        Returns:
            List of categories
        """
        # Use the CATEGORY_MAPPINGS to find relevant categories
        categories = []
        
        # Check if this is a paired topic (contains ":")
        if ":" in topic:
            primary_house, secondary_house = topic.split(":", 1)
            
            self.logger.debug(f"Processing paired topic: primary={primary_house}, secondary={secondary_house}")
            
            # Get the primary category
            primary_category = await self.category_repository.get_by_name(primary_house)
            if not primary_category:
                self.logger.warning(f"Primary category {primary_house} not found in database")
                return categories
                
            # Get the secondary category
            secondary_category = await self.category_repository.get_by_name(secondary_house)
            if not secondary_category:
                self.logger.warning(f"Secondary category {secondary_house} not found in database")
                return categories
                
            # Add the categories
            categories.append(primary_category)
            categories.append(secondary_category)
            
            # Try to find combinations for these two categories
            combinations = await self.category_repository.get_combinations_by_categories(
                primary_category.id, secondary_category.id
            )
            
            if combinations:
                self.logger.debug(f"Found {len(combinations)} combinations for {primary_house} and {secondary_house}")
                # We could add more categories from these combinations if needed
            else:
                self.logger.debug(f"No combinations found for {primary_house} and {secondary_house}")
                
            return categories
            
        # If it's a single category name in CATEGORY_MAPPINGS
        if topic in self.CATEGORY_MAPPINGS:
            # Try to find the category in the database
            category = await self.category_repository.get_by_name(topic)
            if category:
                categories.append(category)
                self.logger.debug(f"Found category for direct topic match: {topic}")
                return categories
            else:
                # If the category doesn't exist in the database yet, we'll need to create it
                self.logger.warning(f"Category {topic} not found in database but exists in CATEGORY_MAPPINGS")
                # For now, continue searching by meaning
        
        # Search for categories with matching Thai meanings
        for category_name, details in self.CATEGORY_MAPPINGS.items():
            thai_meaning = details.get('thai_meaning', '')
            
            # Check if this category is relevant to the topic
            if topic.lower() in thai_meaning.lower() or category_name.lower() == topic.lower():
                # Try to find the category in the database
                category = await self.category_repository.get_by_name(category_name)
                if category:
                    categories.append(category)
                    self.logger.debug(f"Found category {category_name} with relevant Thai meaning: {thai_meaning}")
        
        if not categories:
            self.logger.warning(f"No categories found for topic: {topic}")
            
            # As a last resort, try to look up the exact topic name
            try:
                category = await self.category_repository.get_by_name(topic)
                if category:
                    categories.append(category)
                    self.logger.debug(f"Found category by exact name: {topic}")
            except Exception as e:
                self.logger.error(f"Error finding category by name: {str(e)}")
        
        return categories
    
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

    async def enrich_bases_with_categories(self, bases_result: BasesResult) -> Dict[str, List[Dict[str, Any]]]:
        """
        Enrich bases result from calculator with category details from database.
        This adds the Thai meanings for each position to make it easier for AI to understand.
        
        Args:
            bases_result: The bases result from calculator
            
        Returns:
            Dictionary with enriched bases including category details
        """
        self.logger.info("Enriching bases with category details from database")
        
        if not bases_result or not bases_result.bases:
            self.logger.error("Invalid calculator result: missing bases")
            raise MeaningExtractionError("Invalid calculator result: missing bases")
        
        # Get Thai position names from calculator
        thai_positions = {
            1: self.day_labels if hasattr(self, 'day_labels') else ['อัตตะ', 'หินะ', 'ธานัง', 'ปิตา', 'มาตา', 'โภคา', 'มัชฌิมา'],
            2: self.month_labels if hasattr(self, 'month_labels') else ['ตะนุ', 'กดุมภะ', 'สหัชชะ', 'พันธุ', 'ปุตตะ', 'อริ', 'ปัตนิ'],
            3: self.year_labels if hasattr(self, 'year_labels') else ['มรณะ', 'สุภะ', 'กัมมะ', 'ลาภะ', 'พยายะ', 'ทาสา', 'ทาสี']
        }
        
        result = {}
        
        # Process each base
        for base_num in range(1, 5):
            base_key = f"base{base_num}"
            base_values = getattr(bases_result.bases, base_key)
            
            if not base_values or len(base_values) != 7:
                self.logger.warning(f"Invalid values for {base_key}: {base_values}")
                result[base_key] = []
                continue
            
            enriched_positions = []
            
            # Process each position
            for position in range(7):
                position_num = position + 1  # Convert to 1-indexed
                value = base_values[position]
                
                # Get the Thai position name
                thai_position_name = ""
                if base_num < 4 and position < len(thai_positions[base_num]):
                    thai_position_name = thai_positions[base_num][position]
                    self.logger.debug(f"Position {position_num} in Base {base_num} corresponds to '{thai_position_name}'")
                
                # Create position data
                position_data = {
                    "position": position_num,
                    "value": value,
                    "name": thai_position_name
                }
                
                # If we have a position name, get category details
                if thai_position_name:
                    try:
                        # Query the database for the category
                        category = await self.category_repository.get_by_name(thai_position_name)
                        
                        if category:
                            position_data.update({
                                "category_id": category.id,
                                "thai_meaning": category.thai_meaning if hasattr(category, 'thai_meaning') else "",
                                "house_number": category.house_number if hasattr(category, 'house_number') else None,
                                "house_type": category.house_type if hasattr(category, 'house_type') else "",
                                "found_in_db": True
                            })
                            self.logger.debug(f"Found category for {thai_position_name}: ID={category.id}, Meaning='{getattr(category, 'thai_meaning', '')}'")
                        else:
                            # Fallback to hardcoded values if available
                            position_data.update({
                                "category_id": None,
                                "thai_meaning": self.CATEGORY_MAPPINGS.get(thai_position_name, {}).get('thai_meaning', ""),
                                "house_number": self.CATEGORY_MAPPINGS.get(thai_position_name, {}).get('house_number', None),
                                "house_type": self.CATEGORY_MAPPINGS.get(thai_position_name, {}).get('house_type', ""),
                                "found_in_db": False
                            })
                            self.logger.debug(f"No category found for {thai_position_name}, using fallback values")
                    except Exception as e:
                        self.logger.warning(f"Error getting category for {thai_position_name}: {str(e)}")
                        # Fallback to hardcoded values
                        position_data.update({
                            "category_id": None,
                            "thai_meaning": self.CATEGORY_MAPPINGS.get(thai_position_name, {}).get('thai_meaning', ""),
                            "house_number": self.CATEGORY_MAPPINGS.get(thai_position_name, {}).get('house_number', None),
                            "house_type": self.CATEGORY_MAPPINGS.get(thai_position_name, {}).get('house_type', ""),
                            "found_in_db": False,
                            "error": str(e)
                        })
                
                enriched_positions.append(position_data)
            
            result[base_key] = enriched_positions
        
        self.logger.info(f"Successfully enriched {len(result)} bases with category details")
        return result

    async def extract_meanings_from_bases(self, bases_result: BasesResult) -> MeaningCollection:
        """
        Extract meanings from bases by enriching them with category details first
        This is a simplified version of extract_meanings that doesn't use questions for filtering
        
        Args:
            bases_result: The result from calculator.py containing the bases
            
        Returns:
            Collection of meanings derived from the enriched bases
        """
        try:
            self.logger.info("Extracting meanings from bases")
            
            # Enrich bases with category details
            enriched_bases = await self.enrich_bases_with_categories(bases_result)
            
            meanings = []
            
            # Process each base (1-4)
            for base_num in range(1, 5):
                base_key = f"base{base_num}"
                enriched_positions = enriched_bases.get(base_key, [])
                
                for position_data in enriched_positions:
                    position_num = position_data["position"]
                    value = position_data["value"]
                    category_id = position_data.get("category_id")
                    thai_position_name = position_data.get("name", "")
                    
                    if not category_id and not thai_position_name:
                        self.logger.debug(f"No category or position name for {base_key} position {position_num}")
                        continue
                    
                    try:
                        # Try different approaches to get readings
                        readings = []
                        
                        # 1. If we have a category ID, try to get readings by category
                        if category_id:
                            readings = await self.reading_repository.get_by_categories([category_id])
                            self.logger.debug(f"Found {len(readings)} readings by category ID {category_id}")
                        
                        # 2. If no readings by category or no category ID, try by base and position
                        if not readings:
                            readings = await self.reading_repository.get_by_base_and_position(base_num, position_num)
                            self.logger.debug(f"Found {len(readings)} readings by base {base_num}, position {position_num}")
                        
                        # 3. If still no readings and we have a position name, try by category name
                        if not readings and thai_position_name:
                            category = await self.category_repository.get_by_name(thai_position_name)
                            if category:
                                readings = await self.reading_repository.get_by_categories([category.id])
                                self.logger.debug(f"Found {len(readings)} readings by category name {thai_position_name}")
                        
                        # Process the readings we found
                        for reading in readings:
                            try:
                                # Get the meaning content from the reading
                                meaning_content = ""
                                if hasattr(reading, 'content'):
                                    meaning_content = reading.content
                                elif hasattr(reading, 'meaning'):
                                    meaning_content = reading.meaning
                                elif hasattr(reading, 'thai_content'):
                                    meaning_content = reading.thai_content
                                
                                # Get the heading from the reading
                                heading = ""
                                if hasattr(reading, 'heading'):
                                    heading = reading.heading
                                else:
                                    # Construct a heading if not available
                                    base_name = ""
                                    if base_num == 1:
                                        base_name = "ฐานวันเกิด"
                                    elif base_num == 2:
                                        base_name = "ฐานเดือนเกิด"
                                    elif base_num == 3:
                                        base_name = "ฐานปีเกิด"
                                    elif base_num == 4:
                                        base_name = "ฐานรวม"
                                    
                                    heading = f"{base_name} ตำแหน่ง {position_num} ({thai_position_name})"
                                
                                # Get influence type if available
                                influence_type = "ปานกลาง"  # Default to neutral
                                if hasattr(reading, 'influence_type') and reading.influence_type:
                                    influence_type = reading.influence_type
                                
                                # Calculate match score based on relevance
                                match_score = 5.0  # Default score
                                
                                # Adjust score based on base type (day, month, year bases are more important)
                                if base_num < 4:
                                    match_score += 1.0
                                
                                # Adjust score based on value significance
                                if value in [1, 5, 7]:  # These values are often considered significant
                                    match_score += 0.5
                                
                                # Create meaning with additional metadata
                                meaning = Meaning(
                                    base=base_num,
                                    position=position_num,
                                    value=value,
                                    heading=heading,
                                    meaning=meaning_content,
                                    category=thai_position_name,
                                    match_score=match_score,
                                    metadata={
                                        "thai_meaning": position_data.get("thai_meaning", ""),
                                        "house_number": position_data.get("house_number", None),
                                        "house_type": position_data.get("house_type", ""),
                                        "influence_type": influence_type,
                                        "reading_id": reading.id if hasattr(reading, 'id') else None
                                    }
                                )
                                
                                meanings.append(meaning)
                                self.logger.debug(f"Added meaning for Base {base_num}, Position {position_num}, Value {value}")
                                
                            except Exception as inner_e:
                                self.logger.error(f"Error processing reading: {str(inner_e)}")
                                continue
                    
                    except Exception as position_e:
                        self.logger.error(f"Error processing position {position_num} in base {base_num}: {str(position_e)}")
                        continue
            
            # Sort meanings by match score (highest first)
            meanings.sort(key=lambda m: getattr(m, 'match_score', 0), reverse=True)
            
            # Limit to a reasonable number of meanings
            if len(meanings) > 20:
                meanings = meanings[:20]
            
            # Create and return collection
            result = MeaningCollection(items=meanings)
            self.logger.info(f"Extracted {len(meanings)} meanings from bases")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting meanings from bases: {str(e)}", exc_info=True)
            raise MeaningExtractionError(f"Error extracting meanings from bases: {str(e)}")

    async def get_enriched_birth_chart(self, birth_date: datetime, thai_day: str, question: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a complete enriched birth chart with calculator results and category details
        
        Args:
            birth_date: User's birth date
            thai_day: Thai day of the week
            question: Optional question for focus readings
            
        Returns:
            Dictionary containing the birth info, enriched bases with Thai meanings, and relevant meanings
        """
        try:
            self.logger.info(f"Generating enriched birth chart for {birth_date}, {thai_day}")
            
            # Get calculator service
            from app.services.calculator import CalculatorService
            calculator = CalculatorService()
            
            # Calculate bases
            bases_result = calculator.calculate_birth_bases(birth_date, thai_day)
            
            # Enrich bases with category details
            enriched_bases = await self.enrich_bases_with_categories(bases_result)
            
            # Process focus readings if question is provided
            focus_meanings = None
            if question:
                focus_meanings = await self.extract_meanings(bases_result.bases, question)
            
            # Get general readings without question filtering
            general_meanings = await self.extract_meanings_from_bases(bases_result)
            
            # Create a positions summary with Thai meanings for easy reference by AI
            positions_summary = {}
            for base_num in range(1, 4):  # Only summarize bases 1-3 (day, month, year)
                base_key = f"base{base_num}"
                for pos in enriched_bases.get(base_key, []):
                    if pos.get("name") and pos.get("thai_meaning"):
                        positions_summary[pos["name"]] = {
                            "thai_meaning": pos["thai_meaning"],
                            "base": base_num,
                            "position": pos["position"],
                            "value": pos["value"]
                        }
            
            # Prepare the response with optimized general_meanings structure
            result = {
                "birth_info": {
                    "date": birth_date.isoformat(),
                    "day": thai_day,
                    "day_value": bases_result.birth_info.day_value,
                    "month": bases_result.birth_info.month,
                    "year_animal": bases_result.birth_info.year_animal,
                    "year_start_number": bases_result.birth_info.year_start_number
                },
                "enriched_bases": enriched_bases,
                "positions_summary": positions_summary,  # Add the positions summary for AI reference
                "general_meanings": {
                    "base1": {
                        "name": "ฐานวันเกิด",
                        "meanings": [m.dict() for m in general_meanings.items if m.base == 1]
                    },
                    "base2": {
                        "name": "ฐานเดือนเกิด",
                        "meanings": [m.dict() for m in general_meanings.items if m.base == 2]
                    },
                    "base3": {
                        "name": "ฐานปีเกิด",
                        "meanings": [m.dict() for m in general_meanings.items if m.base == 3]
                    },
                    "base4": {
                        "name": "ฐานรวม",
                        "meanings": [m.dict() for m in general_meanings.items if m.base == 4]
                    }
                },
                "focus_meanings": [meaning.dict() for meaning in focus_meanings.items] if focus_meanings else []
            }
            
            # Add a summary of the bases
            result["bases_summary"] = {
                "base1": bases_result.bases.base1,
                "base2": bases_result.bases.base2,
                "base3": bases_result.bases.base3,
                "base4": bases_result.bases.base4
            }
            
            self.logger.info(f"Successfully generated enriched birth chart with " +
                            f"{len(result['general_meanings'])} general meanings and " +
                            f"{len(result['focus_meanings'])} focus meanings")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating enriched birth chart: {str(e)}", exc_info=True)
            raise MeaningExtractionError(f"Error generating enriched birth chart: {str(e)}")