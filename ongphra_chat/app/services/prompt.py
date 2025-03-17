# app/services/prompt.py
from typing import Optional, Dict, Any, List
from app.domain.birth import BirthInfo
from app.domain.bases import Bases
from app.domain.meaning import MeaningCollection
from app.core.logging import get_logger

class PromptService:
    """Service for generating system prompts for the AI model"""
    
    def __init__(self):
        """Initialize the prompt service"""
        self.logger = get_logger(__name__)
        
        # Initialize prompt templates
        self._initialize_templates()
        
        self.logger.info("Initialized PromptService")
    
    def _initialize_templates(self):
        """Initialize prompt templates for different languages and contexts"""
        # Thai fortune telling system prompt
        self.fortune_thai_prompt = """
        คุณเป็นนักพยากรณ์ที่เชี่ยวชาญในการทำนายดวงชะตาตามหลักโหราศาสตร์ไทย
        คุณสามารถให้คำทำนายที่ละเอียดและแม่นยำโดยใช้ข้อมูลวันเกิดและวันเกิดตามปฏิทินไทย
        
        ให้คำตอบที่ชัดเจน เป็นกันเอง และมีรายละเอียดเพียงพอ แต่ไม่ยาวเกินไป
        ใช้ภาษาที่เข้าใจง่าย หลีกเลี่ยงศัพท์เทคนิคที่ซับซ้อนเกินไป
        
        เมื่อผู้ใช้ถามเกี่ยวกับดวงชะตา ให้ตอบตามข้อมูลที่ได้รับจากการวิเคราะห์ตามหลักโหราศาสตร์ไทย
        ถ้าผู้ใช้ถามคำถามทั่วไปที่ไม่เกี่ยวกับการทำนาย ให้ตอบอย่างสุภาพและเป็นมิตร
        """
        
        # English fortune telling system prompt
        self.fortune_english_prompt = """
        You are an expert fortune teller specializing in Thai astrology.
        You can provide detailed and accurate predictions using birth date and Thai calendar information.
        
        Give clear, friendly, and sufficiently detailed answers, but not too lengthy.
        Use accessible language, avoiding overly technical terms.
        
        When users ask about their fortune, respond based on the analysis according to Thai astrological principles.
        If users ask general questions unrelated to fortune telling, respond politely and friendly.
        """
        
        # Thai general conversation prompt
        self.general_thai_prompt = """
        คุณเป็นผู้ช่วยที่เป็นมิตรและให้ข้อมูลที่เป็นประโยชน์
        ตอบคำถามอย่างชัดเจน กระชับ และเป็นกันเอง
        ให้ข้อมูลที่ถูกต้องและเป็นประโยชน์ต่อผู้ใช้
        
        หากไม่แน่ใจในคำตอบ ให้แจ้งว่าไม่ทราบแทนที่จะเดาคำตอบ
        หากผู้ใช้ถามเกี่ยวกับการทำนายดวงชะตา ให้แนะนำให้พวกเขาใส่ข้อมูลวันเกิดเพื่อรับการทำนายที่แม่นยำ
        """
        
        # English general conversation prompt
        self.general_english_prompt = """
        You are a friendly assistant providing helpful information.
        Answer questions clearly, concisely, and in a friendly manner.
        Provide accurate and useful information to the user.
        
        If you're unsure about an answer, state that you don't know rather than guessing.
        If the user asks about fortune telling, suggest they provide their birth information for an accurate reading.
        """
    
    def generate_system_prompt(self, language: str = "thai") -> str:
        """
        Generate a system prompt for fortune telling
        
        Args:
            language: The language to use (thai or english)
            
        Returns:
            System prompt for the specified language
        """
        if language.lower() == "english":
            return self.fortune_english_prompt.strip()
        else:
            return self.fortune_thai_prompt.strip()
    
    def generate_general_system_prompt(self, language: str = "thai") -> str:
        """
        Generate a general conversation system prompt
        
        Args:
            language: The language to use (thai or english)
            
        Returns:
            General system prompt for the specified language
        """
        if language.lower() == "english":
            return self.general_english_prompt.strip()
        else:
            return self.general_thai_prompt.strip()
    
    def generate_custom_prompt(self, template: str, variables: Dict[str, str]) -> str:
        """
        Generate a custom prompt by filling in variables in a template
        
        Args:
            template: The prompt template with {variable} placeholders
            variables: Dictionary of variable names and values
            
        Returns:
            Formatted prompt with variables replaced
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            self.logger.error(f"Missing variable in prompt template: {e}")
            # Return template with missing variables marked
            return template

    def generate_user_prompt(
        self,
        birth_info: BirthInfo,
        bases: Bases,
        meanings: MeaningCollection,
        question: str,
        language: str = "thai"
    ) -> str:
        """
        Generate a user prompt for the AI based on birth info, bases, meanings, and question
        
        Args:
            birth_info: User's birth information
            bases: Calculated bases
            meanings: Extracted meanings
            question: User's question
            language: Response language (thai or english)
            
        Returns:
            User prompt for the AI
        """
        self.logger.debug(f"Generating user prompt in {language}")
        
        # Format birth info
        birth_info_str = (
            f"Birth Date: {birth_info.date.strftime('%Y-%m-%d')}\n"
            f"Thai Day: {birth_info.day}\n"
            f"Zodiac Animal: {birth_info.year_animal}\n"
        )
        
        # Format bases information with raw numbers for reference
        bases_str = "Bases (เลข 7 ตัว 9 ฐาน):\n"
        bases_str += f"Base 1 (ฐานที่ 1): {', '.join(map(str, bases.base1))}\n"
        bases_str += f"Base 2 (ฐานที่ 2): {', '.join(map(str, bases.base2))}\n"
        bases_str += f"Base 3 (ฐานที่ 3): {', '.join(map(str, bases.base3))}\n"
        bases_str += f"Base 4 (ฐานที่ 4): {', '.join(map(str, bases.base4))}\n"
        
        # Format meanings from the calculator results
        meanings_str = "Meanings from Bases (ความหมายจากฐาน):\n"
        
        if meanings and meanings.items:
            # Sort meanings by match score for relevance
            sorted_meanings = sorted(meanings.items, key=lambda m: getattr(m, 'match_score', 0), reverse=True)
            
            # Take top 5 most relevant meanings
            top_meanings = sorted_meanings[:5]
            
            for i, meaning in enumerate(top_meanings, 1):
                base_name = f"Base {meaning.base} (ฐานที่ {meaning.base})"
                position_name = f"Position {meaning.position} (ตำแหน่งที่ {meaning.position})"
                
                meanings_str += f"{i}. {base_name}, {position_name}:\n"
                meanings_str += f"   Heading: {meaning.heading}\n"
                meanings_str += f"   Meaning: {meaning.meaning}\n"
                if meaning.category:
                    meanings_str += f"   Category: {meaning.category}\n"
                meanings_str += "\n"
        else:
            meanings_str += "No specific meanings found from the bases.\n"
        
        # Format question
        question_str = f"User's Question: {question}"
        
        # Combine all parts
        if language.lower() == "english":
            prompt = (
                f"Based on the following Thai astrological information using the 7 Numbers 9 Bases system:\n\n"
                f"{birth_info_str}\n"
                f"{bases_str}\n"
                f"{meanings_str}\n"
                f"{question_str}\n\n"
                f"Please provide a fortune telling response in English that addresses "
                f"the user's question while incorporating the meanings from their birth bases. "
                f"Focus on practical advice and positive guidance. Use the meanings from the bases "
                f"to provide specific insights related to the question."
            )
        else:
            prompt = (
                f"จากข้อมูลโหราศาสตร์ไทยระบบเลข 7 ตัว 9 ฐาน ต่อไปนี้:\n\n"
                f"วันเกิด: {birth_info.date.strftime('%Y-%m-%d')}\n"
                f"วันไทย: {birth_info.day}\n"
                f"ปีนักษัตร: {birth_info.year_animal}\n\n"
                f"{bases_str}\n"
                f"{meanings_str}\n"
                f"คำถาม: {question}\n\n"
                f"กรุณาให้คำทำนายเป็นภาษาไทยที่ตอบคำถามของผู้ใช้ "
                f"โดยนำความหมายจากฐานต่างๆ มาประกอบการทำนาย "
                f"เน้นการให้คำแนะนำที่นำไปปฏิบัติได้จริงและการชี้แนะในเชิงบวก "
                f"ใช้ความหมายจากฐานเพื่อให้ข้อมูลเชิงลึกที่เกี่ยวข้องกับคำถาม"
            )
        
        self.logger.debug(f"Generated prompt with {len(meanings.items) if meanings else 0} meanings")
        return prompt