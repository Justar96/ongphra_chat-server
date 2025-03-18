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
        Generate a user prompt for fortune telling based on birth information and question
        
        Args:
            birth_info: User's birth information
            bases: Calculated bases
            meanings: Extracted meanings
            question: User's question
            language: Prompt language (thai or english)
            
        Returns:
            Generated prompt for the AI model
        """
        try:
            # Format birth info
            birth_date_str = birth_info.date.strftime("%Y-%m-%d")
            
            # Format bases
            base1_str = ", ".join([str(n) for n in bases.base1])
            base2_str = ", ".join([str(n) for n in bases.base2])
            base3_str = ", ".join([str(n) for n in bases.base3])
            base4_str = ", ".join([str(n) for n in bases.base4])
            
            # Format meanings
            meanings_str = ""
            if meanings and hasattr(meanings, 'items'):
                for meaning in meanings.items:
                    if meaning:
                        meanings_str += f"- {meaning.description}\n"
            
            # Thai day labels
            day_labels = ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
            month_labels = ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"]
            year_labels = ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]
            
            # Create detailed base descriptions with Thai labels
            base1_detail = " | ".join([f"{label}: {value}" for label, value in zip(day_labels, bases.base1)])
            base2_detail = " | ".join([f"{label}: {value}" for label, value in zip(month_labels, bases.base2)])
            base3_detail = " | ".join([f"{label}: {value}" for label, value in zip(year_labels, bases.base3)])
            base4_detail = " | ".join([f"{label}: {value}" for label, value in zip(day_labels, bases.base4)])
            
            # House descriptions
            house_descriptions = {
                "อัตตะ": "ตัวเอง บุคลิกภาพ ร่างกาย",
                "หินะ": "ทรัพย์สิน เงินทอง",
                "ธานัง": "พี่น้อง ญาติพี่น้อง การเดินทาง",
                "ปิตา": "บิดา บ้าน ที่อยู่อาศัย",
                "มาตา": "มารดา บุตร ความรัก",
                "โภคา": "สุขภาพ การงาน ลูกน้อง",
                "มัชฌิมา": "คู่ครอง หุ้นส่วน"
            }
            
            # Add house descriptions
            house_desc_str = "\n".join([f"- {house}: {desc}" for house, desc in house_descriptions.items()])
            
            # Generate prompt based on language
            if language.lower() == "english":
                prompt = f"""
                User's Question: {question}
                
                Birth Information:
                - Birth Date: {birth_date_str}
                - Thai Day: {birth_info.day}
                - Zodiac Animal: {birth_info.year_animal}
                
                Calculated Bases:
                - Base 1 (Day Base): {base1_str}
                  Detailed: {base1_detail}
                - Base 2 (Month Base): {base2_str}
                  Detailed: {base2_detail}
                - Base 3 (Year Base): {base3_str}
                  Detailed: {base3_detail}
                - Base 4 (Sum Base): {base4_str}
                  Detailed: {base4_detail}
                
                House Descriptions:
                {house_desc_str}
                
                Extracted Meanings:
                {meanings_str if meanings_str else "No specific meanings extracted."}
                
                Please provide a fortune telling reading based on this information, focusing on the user's question.
                """
            else:
                prompt = f"""
                คำถามของผู้ใช้: {question}
                
                ข้อมูลวันเกิด:
                - วันเกิด: {birth_date_str}
                - วันไทย: {birth_info.day}
                - ปีนักษัตร: {birth_info.year_animal}
                
                ฐานที่คำนวณได้:
                - ฐาน 1 (ฐานวันเกิด): {base1_str}
                  รายละเอียด: {base1_detail}
                - ฐาน 2 (ฐานเดือนเกิด): {base2_str}
                  รายละเอียด: {base2_detail}
                - ฐาน 3 (ฐานปีเกิด): {base3_str}
                  รายละเอียด: {base3_detail}
                - ฐาน 4 (ฐานรวม): {base4_str}
                  รายละเอียด: {base4_detail}
                
                คำอธิบายภพ:
                {house_desc_str}
                
                ความหมายที่สกัดได้:
                {meanings_str if meanings_str else "ไม่พบความหมายเฉพาะ"}
                
                กรุณาให้คำทำนายตามข้อมูลนี้ โดยเน้นตอบคำถามของผู้ใช้
                """
            
            self.logger.debug(f"Generated user prompt with {len(prompt)} characters")
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error generating user prompt: {str(e)}", exc_info=True)
            
            # Fallback to simple prompt
            if language.lower() == "english":
                return f"User's Question: {question}\n\nPlease provide a fortune telling reading based on Thai astrology."
            else:
                return f"คำถามของผู้ใช้: {question}\n\nกรุณาให้คำทำนายตามหลักโหราศาสตร์ไทย"