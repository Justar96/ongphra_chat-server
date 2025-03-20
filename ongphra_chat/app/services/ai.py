from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from app.config.settings import get_settings
from app.core.logging import get_logger

class AIService:
    """Service for AI-based fortune reading generation"""
    
    def __init__(self):
        """Initialize the AI service"""
        self.logger = get_logger(__name__)
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.default_model
        self.max_tokens = settings.ai_reading_max_tokens
        self.temperature = settings.ai_reading_temperature
        
        self.logger.info(f"Initialized AIService with model {self.model}")
    
    async def generate_reading(
        self,
        birth_info: Dict[str, Any],
        bases: Dict[str, Any],
        topic: str,
        question: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a fortune reading using AI
        
        Args:
            birth_info: Birth information dictionary
            bases: Calculator bases dictionary
            topic: Detected topic
            question: Optional user question
            
        Returns:
            Generated reading text or None if generation fails
        """
        try:
            # Create system prompt
            system_prompt = (
                "คุณคือหมอดูผู้เชี่ยวชาญในการทำนายดวงชะตาจากฐานเกิด "
                "ให้คำทำนายที่ละเอียด แม่นยำ และมีประโยชน์ต่อผู้ถาม "
                "ใช้ภาษาที่สุภาพ เข้าใจง่าย และให้กำลังใจ"
            )
            
            # Create user prompt with birth info and bases
            user_prompt = (
                f"วิเคราะห์ดวงชะตาจากข้อมูลต่อไปนี้:\n"
                f"วันเกิด: {birth_info['date']}\n"
                f"วัน: {birth_info['day']}\n"
                f"ปีนักษัตร: {birth_info['year_animal']}\n\n"
                f"ฐานวันเกิด: {bases['base1']}\n"
                f"ฐานเดือนเกิด: {bases['base2']}\n"
                f"ฐานปีเกิด: {bases['base3']}\n"
                f"ฐานรวม: {bases['base4']}\n\n"
            )
            
            if question:
                user_prompt += f"คำถาม: {question}\n"
            if topic and topic != "ทั่วไป":
                user_prompt += f"หัวข้อที่สนใจ: {topic}\n"
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            if response and response.choices:
                return response.choices[0].message.content.strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating AI reading: {str(e)}", exc_info=True)
            return None

# Factory function for dependency injection
def get_ai_service() -> AIService:
    """Get AI service instance"""
    return AIService() 