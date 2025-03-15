from typing import Optional, Dict, Any, List
from app.domain.birth import BirthInfo
from app.domain.bases import Bases
from app.domain.meaning import MeaningCollection

class PromptService:
    """Service for generating prompts for the AI"""
    
    def generate_system_prompt(self, language: str = "thai") -> str:
        """
        Generate a system prompt for the AI based on language
        
        Args:
            language: Response language (thai or english)
            
        Returns:
            System prompt for the AI
        """
        if language.lower() == "english":
            return """
            You are a Thai fortune teller specializing in the 7 Numbers 9 Bases system.
            Your responses should be insightful, personalized, and focused on the user's question.
            
            IMPORTANT GUIDELINES:
            1. DO NOT mention the raw base numbers in your response. Instead, interpret their meanings directly.
            2. DO NOT list out all the base values (like base1: [4,5,6,7,1,2,3]). Focus on the interpretation.
            3. Provide specific, actionable advice based on the meanings provided.
            4. Be respectful, wise, and compassionate in your tone.
            5. Structure your response in a clear, readable format with paragraphs and bullet points when appropriate.
            6. Relate your interpretation directly to the user's question.
            7. Conclude with practical advice or a positive message.
            
            Remember, you are helping someone understand their fortune through traditional Thai wisdom.
            """
        else:
            return """
            คุณเป็นหมอดูไทยที่เชี่ยวชาญในระบบเลข 7 ตัว 9 ฐาน
            คำตอบของคุณควรมีความลึกซึ้ง เป็นส่วนตัว และมุ่งเน้นไปที่คำถามของผู้ใช้
            
            คำแนะนำสำคัญ:
            1. อย่าพูดถึงตัวเลขฐานดิบในคำตอบของคุณ แต่ให้ตีความหมายของมันโดยตรง
            2. อย่าแสดงค่าฐานทั้งหมด (เช่น ฐาน1: [4,5,6,7,1,2,3]) ให้มุ่งเน้นที่การตีความ
            3. ให้คำแนะนำที่เฉพาะเจาะจงและปฏิบัติได้จริงตามความหมายที่ให้มา
            4. ใช้โทนเสียงที่เคารพ ฉลาด และเห็นอกเห็นใจ
            5. จัดโครงสร้างคำตอบของคุณในรูปแบบที่ชัดเจน อ่านง่าย ด้วยย่อหน้าและจุดสำคัญเมื่อเหมาะสม
            6. เชื่อมโยงการตีความของคุณโดยตรงกับคำถามของผู้ใช้
            7. สรุปด้วยคำแนะนำที่ปฏิบัติได้จริงหรือข้อความเชิงบวก
            
            จำไว้ว่าคุณกำลังช่วยให้ใครบางคนเข้าใจโชคชะตาของพวกเขาผ่านภูมิปัญญาไทยโบราณ
            """
    
    def generate_general_system_prompt(self, language: str = "thai") -> str:
        """
        Generate a general system prompt for the AI when no birth info is provided
        
        Args:
            language: Response language (thai or english)
            
        Returns:
            General system prompt for the AI
        """
        if language.lower() == "english":
            return """
            You are a Thai fortune teller specializing in the 7 Numbers 9 Bases system.
            The user has not provided their birth information, so you cannot give a personalized reading.
            
            Instead, provide general information about the 7 Numbers 9 Bases system and how it works.
            Explain that you need their birth date and Thai day to provide a personalized reading.
            
            Be warm, welcoming, and encourage them to provide their birth information for a more accurate reading.
            """
        else:
            return """
            คุณเป็นหมอดูไทยที่เชี่ยวชาญในระบบเลข 7 ตัว 9 ฐาน
            ผู้ใช้ยังไม่ได้ให้ข้อมูลวันเกิด คุณจึงไม่สามารถให้คำทำนายส่วนบุคคลได้
            
            แทนที่จะให้คำทำนายส่วนบุคคล ให้ข้อมูลทั่วไปเกี่ยวกับระบบเลข 7 ตัว 9 ฐานและวิธีการทำงาน
            อธิบายว่าคุณต้องการวันเกิดและวันไทยของพวกเขาเพื่อให้คำทำนายส่วนบุคคล
            
            ใช้ภาษาที่อบอุ่น เป็นมิตร และกระตุ้นให้พวกเขาให้ข้อมูลวันเกิดเพื่อการทำนายที่แม่นยำยิ่งขึ้น
            """
    
    def generate_user_prompt(
        self,
        birth_info: Optional[BirthInfo],
        bases: Optional[Bases],
        meanings: Optional[MeaningCollection],
        question: str,
        language: str = "thai"
    ) -> str:
        """
        Generate a user prompt for the AI based on birth info, bases, and question
        
        Args:
            birth_info: User's birth information
            bases: Calculated bases
            meanings: Extracted meanings
            question: User's question
            language: Response language (thai or english)
            
        Returns:
            User prompt for the AI
        """
        # Start with the question
        if language.lower() == "english":
            prompt = f"The user's question is: {question}\n\n"
        else:
            prompt = f"คำถามของผู้ใช้คือ: {question}\n\n"
        
        # Add birth info if available
        if birth_info:
            if language.lower() == "english":
                prompt += f"Birth Information:\n"
                prompt += f"- Date: {birth_info.date.strftime('%Y-%m-%d')}\n"
                prompt += f"- Thai Day: {birth_info.day}\n"
                prompt += f"- Day Value: {birth_info.day_value}\n"
                prompt += f"- Month: {birth_info.month}\n"
                prompt += f"- Year Animal: {birth_info.year_animal}\n"
                prompt += f"- Year Start Number: {birth_info.year_start_number}\n\n"
            else:
                prompt += f"ข้อมูลวันเกิด:\n"
                prompt += f"- วันที่: {birth_info.date.strftime('%Y-%m-%d')}\n"
                prompt += f"- วันไทย: {birth_info.day}\n"
                prompt += f"- ค่าวัน: {birth_info.day_value}\n"
                prompt += f"- เดือน: {birth_info.month}\n"
                prompt += f"- ปีนักษัตร: {birth_info.year_animal}\n"
                prompt += f"- เลขเริ่มต้นปี: {birth_info.year_start_number}\n\n"
        
        # Add meanings if available
        if meanings and meanings.items:
            if language.lower() == "english":
                prompt += "Relevant Meanings for the Question:\n"
                for i, meaning in enumerate(meanings.items, 1):
                    prompt += f"{i}. Base {meaning.base}, Position {meaning.position}, Value {meaning.value}:\n"
                    prompt += f"   Heading: {meaning.heading}\n"
                    prompt += f"   Meaning: {meaning.meaning}\n"
                    if meaning.category:
                        prompt += f"   Category: {meaning.category}\n"
                    prompt += "\n"
            else:
                prompt += "ความหมายที่เกี่ยวข้องกับคำถาม:\n"
                for i, meaning in enumerate(meanings.items, 1):
                    prompt += f"{i}. ฐาน {meaning.base}, ตำแหน่ง {meaning.position}, ค่า {meaning.value}:\n"
                    prompt += f"   หัวข้อ: {meaning.heading}\n"
                    prompt += f"   ความหมาย: {meaning.meaning}\n"
                    if meaning.category:
                        prompt += f"   หมวดหมู่: {meaning.category}\n"
                    prompt += "\n"
        
        # Add instructions for the response
        if language.lower() == "english":
            prompt += """
            IMPORTANT: In your response:
            1. DO NOT mention the raw base numbers or list them out.
            2. Focus on interpreting the meanings in a way that's relevant to the user's question.
            3. Provide specific, actionable advice based on the meanings.
            4. Structure your response in a clear, readable format.
            5. Be respectful, wise, and compassionate in your tone.
            6. Conclude with practical advice or a positive message.
            """
        else:
            prompt += """
            สำคัญ: ในคำตอบของคุณ:
            1. อย่าพูดถึงตัวเลขฐานดิบหรือแสดงรายการของพวกมัน
            2. มุ่งเน้นไปที่การตีความความหมายในแบบที่เกี่ยวข้องกับคำถามของผู้ใช้
            3. ให้คำแนะนำที่เฉพาะเจาะจงและปฏิบัติได้จริงตามความหมาย
            4. จัดโครงสร้างคำตอบของคุณในรูปแบบที่ชัดเจน อ่านง่าย
            5. ใช้โทนเสียงที่เคารพ ฉลาด และเห็นอกเห็นใจ
            6. สรุปด้วยคำแนะนำที่ปฏิบัติได้จริงหรือข้อความเชิงบวก
            """
        
        return prompt
