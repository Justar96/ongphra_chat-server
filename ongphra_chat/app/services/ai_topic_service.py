from typing import Dict, List, Optional, Any
import time
import hashlib
import json
from app.core.logging import get_logger
from app.config.settings import Settings, get_settings
from functools import lru_cache
from openai import AsyncOpenAI

class AITopicService:
    """Service for AI-powered topic detection and analysis"""
    
    def __init__(self):
        """Initialize the AI topic service"""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.settings = get_settings()
        self.logger.info("Initialized AITopicService")
        
        # Standard topic list - used only for fallback and to provide structure
        self.standard_topics = [
            'การเงิน', 'ความรัก', 'สุขภาพ', 'การงาน', 'การศึกษา', 
            'ครอบครัว', 'โชคลาภ', 'อนาคต', 'การเดินทาง'
        ]
        
        # Initialize OpenAI client
        self.openai_api_key = self.settings.openai_api_key
        self.default_model = self.settings.default_model
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # In-memory cache for topic detection results
        self._topic_cache = {}
    
    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for a text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_cached_topic(self, text: str) -> Optional[Dict[str, Any]]:
        """Get cached topic detection result if available"""
        cache_key = self._get_cache_key(text)
        if cache_key in self._topic_cache:
            cached_item = self._topic_cache[cache_key]
            # Check if cache is still valid (24 hours)
            if time.time() - cached_item["timestamp"] < 86400:
                self.logger.debug(f"Using cached topic detection for key: {cache_key[:6]}...")
                return cached_item["data"]
        return None
    
    def _cache_topic(self, text: str, result: Dict[str, Any]) -> None:
        """Cache a topic detection result"""
        cache_key = self._get_cache_key(text)
        self._topic_cache[cache_key] = {
            "data": result,
            "timestamp": time.time()
        }
        self.logger.debug(f"Cached topic detection for key: {cache_key[:6]}...")
        
        # Limit cache size
        if len(self._topic_cache) > 1000:  # Arbitrary limit
            # Remove oldest items
            oldest_keys = sorted(
                self._topic_cache.keys(), 
                key=lambda k: self._topic_cache[k]["timestamp"]
            )[:200]  # Remove 200 oldest items
            for key in oldest_keys:
                del self._topic_cache[key]
    
    async def detect_topic(self, user_message: str) -> Dict[str, Any]:
        """
        Detect the most relevant topic from a user message using AI
        
        Args:
            user_message: The user's message/question
            
        Returns:
            Dictionary containing:
            - primary_topic: The main detected topic
            - confidence: Confidence score (0-10)
            - reasoning: Explanation of why this topic was chosen
            - secondary_topics: List of other potential topics
        """
        self.logger.info(f"Detecting topic for message: {user_message[:50]}...")
        
        # Check cache first
        cached_result = self._get_cached_topic(user_message)
        if cached_result:
            return cached_result
        
        try:
            # Use OpenAI API for topic detection
            system_prompt = """
            คุณเป็นผู้เชี่ยวชาญในการวิเคราะห์หัวข้อของคำถามเกี่ยวกับโหราศาสตร์ไทย
            งานของคุณคือการวิเคราะห์ว่าคำถามของผู้ใช้เกี่ยวข้องกับหัวข้อใดมากที่สุด
            
            ให้วิเคราะห์คำถามและระบุหัวข้อหลักจากรายการต่อไปนี้:
            - การเงิน (เงิน ทรัพย์ รายได้ ธุรกิจ การเงิน เศรษฐกิจ ค้าขาย ลงทุน หุ้น)
            - ความรัก (ความสัมพันธ์ คู่ครอง แฟน สามี ภรรยา)
            - สุขภาพ (ร่างกาย จิตใจ โรค อาการป่วย รักษา)
            - การงาน (อาชีพ งาน บริษัท ตำแหน่ง เลื่อนตำแหน่ง)
            - การศึกษา (เรียน สอบ โรงเรียน มหาวิทยาลัย)
            - ครอบครัว (พ่อ แม่ ลูก ญาติ บ้าน)
            - โชคลาภ (โชค ลาภ รางวัล หวย ล็อตเตอรี่)
            - อนาคต (ชะตาชีวิต อนาคต ทำนาย โหราศาสตร์)
            - การเดินทาง (ท่องเที่ยว ย้ายถิ่น ต่างประเทศ)
            
            ตอบในรูปแบบ JSON ที่มีโครงสร้างดังนี้:
            {
              "primary_topic": "หัวข้อหลัก",
              "confidence": [คะแนนความมั่นใจ 1-10],
              "reasoning": "เหตุผลว่าทำไมเลือกหัวข้อนี้",
              "secondary_topics": ["หัวข้อรอง1", "หัวข้อรอง2"]
            }
            
            โปรดตอบเฉพาะ JSON เท่านั้น ไม่ต้องอธิบายเพิ่มเติม
            """
            
            user_prompt = f"วิเคราะห์หัวข้อของคำถามต่อไปนี้: {user_message}"
            
            # Call the OpenAI API
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more deterministic results
                max_tokens=300
            )
            
            # Extract the response
            response_text = response.choices[0].message.content.strip()
            self.logger.debug(f"AI response for topic detection: {response_text}")
            
            # Parse the JSON response
            try:
                result = json.loads(response_text)
                
                # Validate result structure and ensure all required fields are present
                if not all(key in result for key in ["primary_topic", "confidence", "reasoning", "secondary_topics"]):
                    raise ValueError("Missing required fields in AI response")
                
                # Ensure primary_topic is in standard topics list, otherwise use "อนาคต" as fallback
                if result["primary_topic"] not in self.standard_topics:
                    self.logger.warning(f"AI returned non-standard topic '{result['primary_topic']}', using fallback")
                    # Try to map to the closest standard topic or use "อนาคต" as default
                    result["primary_topic"] = "อนาคต"
                
                # Ensure confidence is a number between 1-10
                try:
                    result["confidence"] = float(result["confidence"])
                    result["confidence"] = max(1.0, min(10.0, result["confidence"]))
                except (ValueError, TypeError):
                    result["confidence"] = 5.0  # Default confidence if invalid
                
                # Filter secondary topics to standard list
                result["secondary_topics"] = [topic for topic in result.get("secondary_topics", []) 
                                             if topic in self.standard_topics and topic != result["primary_topic"]]
                
                # Limit to top 2 secondary topics
                result["secondary_topics"] = result["secondary_topics"][:2]
                
                # Cache the validated result
                self._cache_topic(user_message, result)
                
                self.logger.info(f"AI detected topic: {result['primary_topic']} with confidence {result['confidence']}")
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to parse AI response: {str(e)}")
                # Fallback logic
                fallback_result = {
                    "primary_topic": "อนาคต",  # Default fallback topic
                    "confidence": 3.0,
                    "reasoning": "ไม่สามารถวิเคราะห์หัวข้อได้จากการตอบของ AI ใช้หัวข้อทั่วไปแทน",
                    "secondary_topics": []
                }
                self._cache_topic(user_message, fallback_result)
                return fallback_result
                
        except Exception as e:
            self.logger.error(f"Error in AI topic detection: {str(e)}", exc_info=True)
            # Fallback when AI fails completely
            fallback_result = {
                "primary_topic": "อนาคต",  # Default fallback topic
                "confidence": 1.0,
                "reasoning": "เกิดข้อผิดพลาดในการวิเคราะห์หัวข้อ ใช้หัวข้อทั่วไปแทน",
                "secondary_topics": []
            }
            self._cache_topic(user_message, fallback_result)
            return fallback_result
    
    async def record_topic_feedback(
        self, 
        user_id: str,
        user_message: str,
        detected_topic: str,
        selected_meaning_id: int,
        feedback_result: str  # "helpful" or "not_helpful"
    ) -> bool:
        """Record feedback about topic detection to improve future results"""
        try:
            # For now, we'll just log the feedback
            # This could be expanded to store in a database and use for training
            self.logger.info(
                f"Feedback recorded - User: {user_id}, Topic: {detected_topic}, "
                f"Meaning: {selected_meaning_id}, Result: {feedback_result}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error recording topic feedback: {str(e)}", exc_info=True)
            return False

# Factory function for dependency injection
@lru_cache()
def get_ai_topic_service() -> AITopicService:
    """Get AI topic service instance"""
    return AITopicService() 