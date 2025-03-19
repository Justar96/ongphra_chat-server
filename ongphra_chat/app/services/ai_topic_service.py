from typing import Dict, List, Optional, Any
import time
import hashlib
from app.core.logging import get_logger
from app.config.settings import Settings

class AITopicService:
    """Service for AI-powered topic detection and analysis"""
    
    def __init__(self):
        """Initialize the AI topic service"""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.settings = Settings()
        self.logger.info("Initialized AITopicService")
        
        # Topic mappings from your existing code
        self.topic_mappings = {
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
        Detect the most relevant topic from a user message
        
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
            # Convert message to lowercase for matching
            message_lower = user_message.lower()
            
            # Enhanced topic detection with weighted keywords and patterns
            topic_weights = {}
            
            # Get base weights from keyword matches
            for topic, keywords in self.topic_mappings.items():
                # Initialize weight for this topic
                weight = 0
                matched_keywords = []
                
                # Weight keywords by importance and position
                for keyword in keywords:
                    # Check for exact matches (higher weight)
                    if f" {keyword} " in f" {message_lower} ":
                        weight += 1.5
                        matched_keywords.append(keyword)
                    # Check for partial matches at word boundaries
                    elif keyword in message_lower:
                        # Check if it's at the beginning or end of message or surrounded by non-Thai characters
                        if (message_lower.startswith(keyword) or 
                            message_lower.endswith(keyword) or 
                            any(f"{keyword}{c}" in message_lower for c in " ,.?!:;") or
                            any(f"{c}{keyword}" in message_lower for c in " ,.?!:;")):
                            weight += 1.0
                            matched_keywords.append(keyword)
                
                # Boost based on question patterns specific to each topic
                topic_patterns = {
                    'การเงิน': ['จะรวย', 'การเงิน.*เป็นอย่างไร', 'เงิน.*ไหม', 'ธุรกิจ.*ไหม', 'ค้าขาย.*ไหม'],
                    'ความรัก': ['จะได้แต่งงาน', 'ความรัก.*เป็นอย่างไร', 'แฟน.*ไหม', 'คู่ครอง.*ไหม'],
                    'สุขภาพ': ['สุขภาพ.*เป็นอย่างไร', 'สุขภาพ.*ไหม', 'ป่วย.*ไหม', 'โรค.*ไหม'],
                    'การงาน': ['งาน.*เป็นอย่างไร', 'ได้เลื่อนตำแหน่ง.*ไหม', 'เปลี่ยนงาน.*ไหม'],
                    'โชคลาภ': ['จะมีโชค.*ไหม', 'ถูกหวย.*ไหม', 'เสี่ยงโชค.*ไหม'],
                    'อนาคต': ['อนาคต.*เป็นอย่างไร', 'ชะตาชีวิต.*อย่างไร', 'ชีวิต.*ไหม']
                }
                
                if topic in topic_patterns:
                    for pattern in topic_patterns[topic]:
                        import re
                        if re.search(pattern, message_lower):
                            weight += 2.0  # Large boost for question pattern matches
                            self.logger.debug(f"Pattern match for '{topic}': {pattern}")
                
                # Assign final weight only if there are matches
                if weight > 0:
                    topic_weights[topic] = {
                        'weight': weight,
                        'matched_keywords': matched_keywords,
                        'keyword_count': len(matched_keywords),
                        'total_keywords': len(keywords)
                    }
            
            # If no topics were found, use context analysis to determine most likely topic
            if not topic_weights:
                # Context words that might indicate topic domains without explicit keywords
                context_indicators = {
                    'การเงิน': ['จ่าย', 'ซื้อ', 'ขาย', 'ตังค์', 'เงินเดือน', 'หนี้', 'ขายของ', 'ตลาด'],
                    'ความรัก': ['ชอบ', 'รัก', 'คนรู้ใจ', 'ผูกพัน', 'อกหัก', 'จริงใจ', 'เข้ากันได้'],
                    'สุขภาพ': ['เจ็บ', 'ปวด', 'อ่อนแรง', 'เหนื่อย', 'นอน', 'พักผ่อน', 'ตรวจ', 'หมอ'],
                    'การงาน': ['ทำงาน', 'บริษัท', 'หัวหน้า', 'เพื่อนร่วมงาน', 'ออฟฟิศ', 'ประชุม'],
                    'อนาคต': ['ชีวิต', 'ดวง', 'ชะตา', 'ทำนาย', 'หมอดู', 'แนวทาง', 'ข้างหน้า']
                }
                
                for topic, indicators in context_indicators.items():
                    matches = sum(1 for word in indicators if word in message_lower)
                    if matches > 0:
                        topic_weights[topic] = {
                            'weight': matches * 0.5,  # Lower weight for context indicators
                            'matched_keywords': [],
                            'keyword_count': matches,
                            'total_keywords': len(indicators)
                        }
            
            # Sort topics by weight
            sorted_topics = sorted(
                topic_weights.items(), 
                key=lambda x: x[1]['weight'], 
                reverse=True
            )
            
            # Default fallback topic with small confidence if nothing is found
            if not sorted_topics:
                primary_topic = 'อนาคต'  # Default fallback
                confidence = 1.0
                reasoning = "ไม่พบคำสำคัญที่เกี่ยวข้องกับหัวข้อเฉพาะ ใช้การทำนายแบบทั่วไป"
                secondary_topics = []
            else:
                # Get primary topic and calculate confidence
                primary_topic, topic_data = sorted_topics[0]
                
                # Calculate confidence score (0-10)
                raw_confidence = min(10.0, topic_data['weight'])
                
                # Adjust confidence based on matched keyword percentage
                if topic_data['total_keywords'] > 0:
                    keyword_ratio = topic_data['keyword_count'] / topic_data['total_keywords']
                    confidence = raw_confidence * (0.5 + 0.5 * keyword_ratio)  # Balance between raw score and ratio
                else:
                    confidence = raw_confidence
                
                # Round to 2 decimal places for readability
                confidence = round(confidence, 2)
                
                # Get secondary topics (topics with at least 40% of the primary topic's weight)
                threshold = topic_data['weight'] * 0.4
                secondary_topics = [
                    topic for topic, data in sorted_topics[1:]
                    if data['weight'] >= threshold
                ]
                
                # Generate reasoning
                matched_words = ", ".join(topic_data['matched_keywords'][:3])  # Show up to 3 matched words
                if matched_words:
                    reasoning = f"คำถามของคุณเกี่ยวข้องกับ{primary_topic} (พบคำสำคัญ: {matched_words})"
                else:
                    reasoning = f"คำถามของคุณน่าจะเกี่ยวข้องกับ{primary_topic}"
                
                if secondary_topics:
                    secondary_topics_str = ", ".join(secondary_topics)
                    reasoning += f" และอาจเกี่ยวข้องกับ {secondary_topics_str}"
            
            result = {
                "primary_topic": primary_topic,
                "confidence": confidence,
                "reasoning": reasoning,
                "secondary_topics": secondary_topics
            }
            
            # Cache the result
            self._cache_topic(user_message, result)
            
            self.logger.info(f"Detected topic: {primary_topic} with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error detecting topic: {str(e)}", exc_info=True)
            return {
                "primary_topic": "อนาคต",  # Default fallback
                "confidence": 1.0,
                "reasoning": "ไม่สามารถวิเคราะห์หัวข้อได้ ใช้การทำนายทั่วไป",
                "secondary_topics": []
            }
    
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
def get_ai_topic_service() -> AITopicService:
    """Get AI topic service instance"""
    return AITopicService() 