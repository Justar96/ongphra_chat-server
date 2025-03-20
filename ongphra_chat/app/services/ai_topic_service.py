from typing import Dict, List, Optional, Any, Set, Tuple
import time
import hashlib
from pydantic import BaseModel, Field
from app.core.logging import get_logger
from app.config.settings import Settings
from functools import lru_cache
import re
from datetime import datetime
from redis import asyncio as aioredis
from redis.exceptions import ConnectionError
from pythainlp import word_tokenize
from pythainlp.util import normalize
from pythainlp.tokenize import word_tokenize
from pythainlp.corpus import thai_stopwords
from app.config.thai_astrology import CATEGORY_MAPPINGS, TOPIC_MAPPINGS

# Pydantic models for type safety and validation
class CategoryMapping(BaseModel):
    thai_meaning: str
    house_number: int
    house_type: str

class UserMapping(BaseModel):
    category: str
    value: int
    base_type: str  # 'day', 'month', 'year', or 'sum'

class MappingAnalysis(BaseModel):
    category: str
    user_value: int
    base_type: str
    thai_meaning: str
    house_number: int
    house_type: str
    significance: str
    relationship_score: float

class TopicFeedback(BaseModel):
    user_id: str
    user_message: str
    detected_topic: str
    selected_meaning_id: int
    feedback_result: str
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence_score: float
    
class TopicDetectionResult(BaseModel):
    primary_topic: str
    confidence: float
    reasoning: str
    secondary_topics: List[str]
    sentiment: Optional[str] = None
    subtopics: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    mapping_analysis: Optional[List[MappingAnalysis]] = None

class AITopicService:
    """Enhanced service for AI-powered Thai topic detection and analysis"""
    
    def __init__(self):
        """Initialize the AI topic service with enhanced Thai language support"""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.settings = Settings()
        self.stopwords = thai_stopwords()
        
        # Initialize category mappings
        self.category_mappings = CATEGORY_MAPPINGS

        self.logger.info("Initialized Enhanced AITopicService with category mappings")
        
        # Initialize Redis connection with fallback to in-memory cache
        self.redis = None
        self._in_memory_cache = {}
        self._redis_failed = False  # Track Redis connection failures
        self._redis_retry_time = 0  # Time to retry Redis connection
        
        try:
            if hasattr(self.settings, 'redis_url'):
                self.redis = aioredis.from_url(
                    self.settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                self.logger.info("Successfully connected to Redis")
            else:
                self.logger.warning("Redis URL not configured, using in-memory cache")
        except Exception as e:
            self._redis_failed = True
            self._redis_retry_time = time.time() + 300  # Retry after 5 minutes
            self.logger.warning(f"Failed to connect to Redis: {str(e)}. Using in-memory cache. Will retry in 5 minutes.")
        
        # Enhanced topic mappings with hierarchical structure
        self.topic_mappings = TOPIC_MAPPINGS
        
        # Thai sentiment words
        self.sentiment_words = {
            'positive': ['ดี', 'เยี่ยม', 'สุข', 'รัก', 'ชอบ', 'สบาย', 'สำเร็จ', 'ยินดี', 'สนุก'],
            'negative': ['แย่', 'เสียใจ', 'ทุกข์', 'เครียด', 'กลัว', 'เจ็บ', 'ผิดหวัง', 'โกรธ'],
            'neutral': ['ปกติ', 'ธรรมดา', 'พอใช้', 'เฉยๆ']
        }

    async def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for a text"""
        return f"topic:{hashlib.md5(text.encode()).hexdigest()}"

    async def _get_cached_topic(self, text: str) -> Optional[TopicDetectionResult]:
        """Get cached topic detection result with improved connection handling"""
        cache_key = await self._get_cache_key(text)
        
        # Only try Redis if we haven't had recent failures
        if not self._redis_failed or time.time() > self._redis_retry_time:
            try:
                if self.redis:
                    cached_data = await self.redis.get(cache_key)
                    if cached_data:
                        self.logger.debug(f"Redis cache hit for key: {cache_key[:6]}...")
                        return TopicDetectionResult.parse_raw(cached_data)
                    
                    # Connection successful, reset failure flag
                    if self._redis_failed:
                        self._redis_failed = False
                        self.logger.info("Redis connection re-established")
            except Exception as e:
                self._redis_failed = True  
                self._redis_retry_time = time.time() + 300  # Retry after 5 minutes
                self.logger.error(f"Redis cache error: {str(e)}. Will retry in 5 minutes")
        
        # Fallback to memory cache
        if cache_key in self._in_memory_cache:
            cached_item = self._in_memory_cache[cache_key]
            if time.time() - cached_item["timestamp"] < 86400:  # 24 hours
                self.logger.debug(f"Memory cache hit for key: {cache_key[:6]}...")
                return cached_item["data"]
            else:
                del self._in_memory_cache[cache_key]
                
        return None

    async def _cache_topic(self, text: str, result: TopicDetectionResult) -> None:
        """Cache a topic detection result in Redis or in-memory"""
        cache_key = await self._get_cache_key(text)
        
        # Only try Redis if we haven't had recent failures
        if not self._redis_failed or time.time() > self._redis_retry_time:
            try:
                if self.redis:
                    await self.redis.set(
                        cache_key,
                        result.json(),
                        ex=86400  # 24 hours expiration
                    )
                    self.logger.debug(f"Cached in Redis for key: {cache_key[:6]}...")
                    
                    # Connection successful, reset failure flag
                    if self._redis_failed:
                        self._redis_failed = False
                        self.logger.info("Redis connection re-established")
                    return
            except Exception as e:
                self._redis_failed = True
                self._redis_retry_time = time.time() + 300  # Retry after 5 minutes
                self.logger.error(f"Redis cache error: {str(e)}. Will retry in 5 minutes")
        
        # Fallback to memory cache
        self._in_memory_cache[cache_key] = {
            "data": result,
            "timestamp": time.time()
        }
        self.logger.debug(f"Cached in memory for key: {cache_key[:6]}...")
        
        # Limit in-memory cache size
        if len(self._in_memory_cache) > 1000:
            oldest_keys = sorted(
                self._in_memory_cache.keys(),
                key=lambda k: self._in_memory_cache[k]["timestamp"]
            )[:200]  # Remove 200 oldest items
            for key in oldest_keys:
                del self._in_memory_cache[key]

    def _preprocess_thai_text(self, text: str) -> str:
        """Preprocess Thai text for better analysis"""
        # Normalize text
        text = normalize(text)
        
        # Tokenize
        tokens = word_tokenize(text, engine="newmm")
        
        # Remove stopwords
        tokens = [token for token in tokens if token not in self.stopwords]
        
        return " ".join(tokens)

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of Thai text"""
        text_lower = text.lower()
        
        # Count sentiment words
        sentiment_scores = {
            'positive': sum(1 for word in self.sentiment_words['positive'] if word in text_lower),
            'negative': sum(1 for word in self.sentiment_words['negative'] if word in text_lower),
            'neutral': sum(1 for word in self.sentiment_words['neutral'] if word in text_lower)
        }
        
        # Determine dominant sentiment
        max_score = max(sentiment_scores.values())
        if max_score == 0:
            return "neutral"
            
        dominant_sentiments = [k for k, v in sentiment_scores.items() if v == max_score]
        return dominant_sentiments[0]

    def analyze_user_mappings(
        self,
        user_mappings: List[UserMapping]
    ) -> List[MappingAnalysis]:
        """
        Analyze user's calculated mappings against standard category mappings
        
        Args:
            user_mappings: List of user's calculated mappings
            
        Returns:
            List of mapping analysis results
        """
        analysis_results = []
        
        for user_map in user_mappings:
            if user_map.category in self.category_mappings:
                cat_info = self.category_mappings[user_map.category]
                
                # Calculate relationship score based on house number and type
                relationship_score = self._calculate_relationship_score(
                    user_map.value,
                    cat_info['house_number'],
                    user_map.base_type,
                    cat_info['house_type']
                )
                
                # Determine significance based on relationship score
                significance = self._determine_significance(relationship_score)
                
                analysis = MappingAnalysis(
                    category=user_map.category,
                    user_value=user_map.value,
                    base_type=user_map.base_type,
                    thai_meaning=cat_info['thai_meaning'],
                    house_number=cat_info['house_number'],
                    house_type=cat_info['house_type'],
                    significance=significance,
                    relationship_score=relationship_score
                )
                
                analysis_results.append(analysis)
        
        return analysis_results

    def _calculate_relationship_score(
        self,
        user_value: int,
        house_number: int,
        base_type: str,
        house_type: str
    ) -> float:
        """Calculate relationship score between user value and house"""
        # Base score from value-house number relationship
        base_score = 1.0 - (abs(user_value - house_number) / 9.0)  # Normalize to 0-1
        
        # Adjust score based on base type and house type
        type_multiplier = {
            'day': {'กาลปักษ์': 1.2, 'เกณฑ์ชะตา': 1.0, 'จร': 0.8},
            'month': {'กาลปักษ์': 0.8, 'เกณฑ์ชะตา': 1.2, 'จร': 1.0},
            'year': {'กาลปักษ์': 0.8, 'เกณฑ์ชะตา': 1.0, 'จร': 1.2},
            'sum': {'กาลปักษ์': 1.0, 'เกณฑ์ชะตา': 1.0, 'จร': 1.0}
        }
        
        return base_score * type_multiplier[base_type][house_type]

    def _determine_significance(self, score: float) -> str:
        """Determine significance level based on relationship score"""
        if score >= 0.8:
            return "สำคัญมาก"
        elif score >= 0.6:
            return "สำคัญ"
        elif score >= 0.4:
            return "ปานกลาง"
        else:
            return "น้อย"

    async def detect_topic(
        self,
        user_message: str,
        user_mappings: Optional[List[UserMapping]] = None
    ) -> TopicDetectionResult:
        """
        Enhanced topic detection with user mapping analysis
        
        Args:
            user_message: The user's message/question
            user_mappings: Optional list of user's calculated mappings
            
        Returns:
            TopicDetectionResult object containing detailed analysis
        """
        self.logger.info(f"Detecting topic for message: {user_message[:50]}...")
        
        # Check cache first
        cached_result = await self._get_cached_topic(user_message)
        if cached_result and not user_mappings:
            return cached_result
            
        try:
            # First check for general reading requests
            general_keywords = ['ทั่วไป', 'ดวงทั่วไป', 'ดูดวงทั่วไป', 'ทำนายทั่วไป', 'ทำนายดวง', 'ดูดวง', 'อนาคต', 'ชีวิต', 'ภาพรวม', 'general', 'overall', 'fortune', 'future', 'life']
            
            # Check for presence of general keywords
            general_count = sum(1 for keyword in general_keywords if keyword.lower() in user_message.lower())
            
            # Check for absence of specific topics
            specific_topics = ['การเงิน', 'เงินทอง', 'ความรัก', 'คู่ครอง', 'สุขภาพ', 'การงาน', 'งาน', 'การศึกษา', 'เรียน', 'ครอบครัว', 'ผลการเรียน', 'เดินทาง']
            specific_count = sum(1 for topic in specific_topics if topic.lower() in user_message.lower())
            
            # If general indicators are present and specific topics are absent, it's likely a general request
            if (general_count > 0 and specific_count == 0) or ("ทั่วไป" in user_message):
                self.logger.info("Detected general reading request")
                return TopicDetectionResult(
                    primary_topic="ทั่วไป",
                    confidence=9.0,
                    reasoning="ผู้ใช้ต้องการคำทำนายในภาพรวมทั่วไป ไม่ได้ระบุหัวข้อเฉพาะ",
                    secondary_topics=[],
                    sentiment=self._analyze_sentiment(user_message),
                    subtopics=[],
                    entities=[],
                    mapping_analysis=self.analyze_user_mappings(user_mappings) if user_mappings else None
                )
            
            # Analyze user mappings if provided
            mapping_analysis = None
            if user_mappings:
                mapping_analysis = self.analyze_user_mappings(user_mappings)

            # Preprocess text
            processed_text = self._preprocess_thai_text(user_message)
            message_lower = processed_text.lower()
            
            # Enhanced topic detection with hierarchical analysis
            topic_scores = {}
            
            for topic, data in self.topic_mappings.items():
                # Initialize topic score
                topic_score = {
                    'weight': 0,
                    'matched_keywords': [],
                    'matched_subtopics': {},
                    'entities': []
                }
                
                # Check main topic keywords
                for keyword in data['keywords']:
                    if keyword in message_lower:
                        topic_score['weight'] += 1.5
                        topic_score['matched_keywords'].append(keyword)
                
                # Check subtopics
                for subtopic, subtopic_keywords in data['subtopics'].items():
                    subtopic_matches = []
                    for keyword in subtopic_keywords:
                        if keyword in message_lower:
                            topic_score['weight'] += 1.0
                            subtopic_matches.append(keyword)
                    
                    if subtopic_matches:
                        topic_score['matched_subtopics'][subtopic] = subtopic_matches
                
                if topic_score['weight'] > 0:
                    topic_scores[topic] = topic_score
            
            # If no direct matches, use context analysis
            if not topic_scores:
                # Implementation remains similar but with enhanced context detection
                pass
            
            # Sort topics by weight
            sorted_topics = sorted(
                topic_scores.items(),
                key=lambda x: x[1]['weight'],
                reverse=True
            )
            
            if not sorted_topics:
                result = TopicDetectionResult(
                    primary_topic="ทั่วไป",
                    confidence=1.0,
                    reasoning="ไม่พบคำสำคัญที่เกี่ยวข้องกับหัวข้อเฉพาะ",
                    secondary_topics=[],
                    sentiment=self._analyze_sentiment(user_message),
                    subtopics=[],
                    entities=[],
                    mapping_analysis=mapping_analysis
                )
            else:
                primary_topic, topic_data = sorted_topics[0]
                
                # Calculate confidence (0-10)
                confidence = min(10.0, topic_data['weight'])
                
                # Get subtopics
                subtopics = list(topic_data['matched_subtopics'].keys())
                
                # Get secondary topics
                threshold = topic_data['weight'] * 0.4
                secondary_topics = [
                    topic for topic, data in sorted_topics[1:]
                    if data['weight'] >= threshold
                ]
                
                # Generate reasoning
                reasoning = f"พบคำสำคัญที่เกี่ยวข้องกับ{primary_topic}"
                if subtopics:
                    reasoning += f" โดยเฉพาะในด้าน{', '.join(subtopics)}"
                
                # Add mapping analysis to result
                result = TopicDetectionResult(
                    primary_topic=primary_topic,
                    confidence=confidence,
                    reasoning=reasoning,
                    secondary_topics=secondary_topics,
                    sentiment=self._analyze_sentiment(user_message),
                    subtopics=subtopics,
                    entities=topic_data['matched_keywords'],
                    mapping_analysis=mapping_analysis
                )
            
            # Cache result only if no user mappings (as they're specific to each request)
            if not user_mappings:
                await self._cache_topic(user_message, result)
            
            self.logger.info(f"Detected topic: {result.primary_topic} with confidence {result.confidence:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error detecting topic: {str(e)}", exc_info=True)
            return TopicDetectionResult(
                primary_topic="ทั่วไป",
                confidence=1.0,
                reasoning="เกิดข้อผิดพลาดในการวิเคราะห์หัวข้อ",
                secondary_topics=[],
                sentiment="neutral",
                subtopics=[],
                entities=[],
                mapping_analysis=None
            )

    async def record_topic_feedback(
        self,
        feedback: TopicFeedback
    ) -> bool:
        """Record feedback about topic detection with enhanced tracking"""
        try:
            # Store feedback in Redis for analysis
            feedback_key = f"feedback:{feedback.user_id}:{int(time.time())}"
            await self.redis.hmset(feedback_key, feedback.dict())
            await self.redis.expire(feedback_key, 60 * 60 * 24 * 30)  # 30 days retention
            
            # Update feedback statistics
            stats_key = f"topic_stats:{feedback.detected_topic}"
            await self.redis.hincrby(stats_key, "total_feedbacks", 1)
            await self.redis.hincrby(
                stats_key,
                "positive_feedbacks",
                1 if feedback.feedback_result == "helpful" else 0
            )
            
            self.logger.info(
                f"Feedback recorded - User: {feedback.user_id}, "
                f"Topic: {feedback.detected_topic}, Result: {feedback.feedback_result}"
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