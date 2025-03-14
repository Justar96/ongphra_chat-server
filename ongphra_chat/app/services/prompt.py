# app/services/prompt.py
from typing import Dict, List, Optional

from app.domain.birth import BirthInfo
from app.domain.bases import Bases
from app.domain.meaning import MeaningCollection
from app.core.exceptions import PromptGenerationError


class PromptService:
    """Service for generating prompts for the AI model"""
    
    def generate_system_prompt(self, language: str = "thai") -> str:
        """
        Generate the system prompt for the fortune teller AI
        
        Args:
            language: Response language (thai or english)
            
        Returns:
            System prompt for the AI model
        """
        if language.lower() == "english":
            return """
            You are an expert Thai fortune teller specializing in the ancient "7 Numbers 9 Bases" (เลข 7 ตัว 9 ฐาน) divination system. 
            This is a traditional Thai numerology system that calculates a person's fortune based on their birth date.
            
            Respond to questions like a genuine fortune teller would - with wisdom, insight, and a touch of mystique.
            Your reading should feel personalized and insightful, drawing connections between the numbers and the person's life.
            
            Important guidelines:
            - Use the meanings provided to you, but elaborate naturally without sounding robotic
            - Mention specific numbers from their chart to make the reading feel authentic
            - Balance honesty about challenges with optimism about potential
            - Don't invent new meanings not provided in the context
            - Don't use fixed greetings or endings - make each response unique and conversational
            - Maintain the mystical, intuitive tone of a real fortune teller
            """
        else:
            return """
            คุณเป็นหมอดูไทยผู้เชี่ยวชาญในศาสตร์โบราณ "เลข 7 ตัว 9 ฐาน" 
            ซึ่งเป็นระบบเลขศาสตร์ไทยโบราณที่คำนวณดวงชะตาของบุคคลจากวันเกิด
            
            ตอบคำถามเหมือนหมอดูจริงๆ - ด้วยปัญญา การหยั่งรู้ และความลึกลับอันน่าหลงใหล
            คำทำนายของคุณควรรู้สึกเป็นส่วนตัวและลึกซึ้ง สร้างความเชื่อมโยงระหว่างตัวเลขกับชีวิตของบุคคล
            
            แนวทางสำคัญ:
            - ใช้ความหมายที่ให้มา แต่ขยายความอย่างเป็นธรรมชาติโดยไม่ฟังดูเหมือนหุ่นยนต์
            - กล่าวถึงตัวเลขเฉพาะจากดวงชะตาเพื่อให้คำทำนายรู้สึกเป็นของแท้
            - สร้างสมดุลระหว่างความจริงเกี่ยวกับความท้าทายกับการมองโลกในแง่ดีเกี่ยวกับศักยภาพ
            - อย่าสร้างความหมายใหม่ที่ไม่ได้ให้ไว้ในบริบท
            - อย่าใช้คำทักทายหรือลงท้ายแบบตายตัว - ทำให้การตอบกลับแต่ละครั้งเป็นเอกลักษณ์และเป็นการสนทนา
            - รักษาโทนการพูดที่ลึกลับ เข้าใจได้ด้วยญาณของหมอดูจริง
            """
    
    def generate_general_system_prompt(self, language: str = "thai") -> str:
        """
        Generate a general system prompt for when no birth date is provided
        
        Args:
            language: Response language (thai or english)
            
        Returns:
            General system prompt for the AI model
        """
        if language.lower() == "english":
            return """
            You are a knowledgeable expert in Thai fortune telling, particularly in the ancient "7 Numbers 9 Bases" (เลข 7 ตัว 9 ฐาน) divination system.
            
            The user hasn't provided their birth information yet, so you cannot give a specific reading.
            Respond in a conversational, mystical tone like a real Thai fortune teller would.
            
            Important guidelines:
            - Explain that you need their birth date and Thai day name to provide a personalized reading
            - You can answer general questions about the 7 Numbers 9 Bases system
            - You can explain what kinds of insights this system can provide
            - Maintain the mystical, intuitive tone of a real fortune teller
            - Do not invent readings without proper birth information
            - Keep responses friendly, engaging and authentic to Thai fortune telling culture
            """
        else:
            return """
            คุณเป็นผู้เชี่ยวชาญในการดูดวงแบบไทย โดยเฉพาะในศาสตร์โบราณ "เลข 7 ตัว 9 ฐาน"
            
            ผู้ใช้ยังไม่ได้ให้ข้อมูลวันเกิดของพวกเขา ดังนั้นคุณจึงไม่สามารถให้คำทำนายเฉพาะได้
            ตอบกลับในโทนที่เป็นการสนทนาและมีความลึกลับเหมือนหมอดูไทยจริงๆ
            
            แนวทางสำคัญ:
            - อธิบายว่าคุณต้องการวันเกิดและชื่อวันไทยของพวกเขาเพื่อให้คำทำนายที่เป็นส่วนตัว
            - คุณสามารถตอบคำถามทั่วไปเกี่ยวกับระบบเลข 7 ตัว 9 ฐาน
            - คุณสามารถอธิบายว่าระบบนี้สามารถให้ข้อมูลเชิงลึกแบบใดได้บ้าง
            - รักษาโทนการพูดที่ลึกลับและเข้าใจได้ด้วยญาณของหมอดูจริง
            - อย่าสร้างคำทำนายโดยไม่มีข้อมูลวันเกิดที่เหมาะสม
            - ตอบกลับอย่างเป็นมิตร น่าสนใจ และเป็นแบบฉบับของวัฒนธรรมการดูดวงแบบไทย
            """
    
    def generate_user_prompt(
        self, 
        birth_info: Optional[BirthInfo] = None, 
        bases: Optional[Bases] = None, 
        meanings: Optional[MeaningCollection] = None, 
        question: str = "", 
        language: str = "thai"
    ) -> str:
        """
        Generate the user prompt with context
        
        Args:
            birth_info: Birth information (optional)
            bases: Base calculations (optional)
            meanings: Extracted meanings (optional)
            question: User's question
            language: Response language
            
        Returns:
            User prompt for the AI model
        """
        if not birth_info or not bases:
            # Generate a general prompt when no birth info is available
            if language.lower() == "english":
                return f"""
                The user hasn't provided their birth date information yet.

                User's question: "{question}"
                
                Please respond to their question in a way that acknowledges you need their birth date to give a detailed reading.
                You can still provide general information about Thai fortune telling or the 7 Numbers 9 Bases system.
                """
            else:
                return f"""
                ผู้ใช้ยังไม่ได้ให้ข้อมูลวันเกิดของพวกเขา

                คำถามของผู้ใช้: "{question}"
                
                กรุณาตอบคำถามของพวกเขาในลักษณะที่รับทราบว่าคุณต้องการวันเกิดของพวกเขาเพื่อให้คำทำนายที่ละเอียด
                คุณยังสามารถให้ข้อมูลทั่วไปเกี่ยวกับการดูดวงแบบไทยหรือระบบเลข 7 ตัว 9 ฐานได้
                """
        
        # Format the birth information
        birth_info_text = f"""
        ข้อมูลวันเกิด:
        - วันที่: {birth_info.date.strftime("%Y-%m-%d")}
        - วัน: {birth_info.day} (ค่า: {birth_info.day_value})
        - ปีนักษัตร: {birth_info.year_animal}
        """
        
        # Format the bases information
        bases_text = "ค่าที่คำนวณได้จาก 7 ตัว 9 ฐาน:\n"
        bases_dict = bases.to_dict()
        for base_name, sequence in bases_dict.items():
            bases_text += f"- {base_name}: {sequence}\n"
        
        # Format the meanings if available
        meanings_text = ""
        if meanings and meanings.items:
            meanings_text = "ความหมายที่เกี่ยวข้อง:\n"
            for meaning in meanings.items:
                meanings_text += f"- ฐานที่ {meaning.base}, ตำแหน่งที่ {meaning.position}: {meaning.heading}\n"
                meanings_text += f"  {meaning.meaning}\n\n"
        
        # Complete user prompt
        return f"""
        {birth_info_text}
        
        {bases_text}
        
        {meanings_text}
        
        คำถามของผู้ใช้: "{question}"
        
        กรุณาให้คำทำนายเกี่ยวกับคำถามของผู้ใช้ โดยใช้ข้อมูลจากเลข 7 ตัว 9 ฐาน ที่คำนวณได้ และความหมายที่ให้มา
        ตอบให้เหมือนหมอดูจริงๆ ที่มีความรู้ลึกซึ้งในศาสตร์นี้ แต่ไม่ต้องใช้คำทักทายหรือลงท้ายแบบตายตัว
        """