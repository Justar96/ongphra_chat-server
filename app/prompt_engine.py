import openai
from typing import Dict, List
from .settings import OPENAI_API_KEY, MODEL_NAME

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

class PromptEngine:
    def __init__(self):
        pass
        
    def generate_system_prompt(self, language="thai"):
        """Generate the system prompt for the fortune teller"""
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
    
    def generate_user_prompt(self, birth_info: Dict, bases: Dict, meanings: List[Dict], question: str):
        """Generate the user prompt with all the context"""
        # Format the birth information
        birth_info_text = f"""
        ข้อมูลวันเกิด:
        - วันที่: {birth_info['date']}
        - วัน: {birth_info['day']} (ค่า: {birth_info['day_value']})
        - ปีนักษัตร: {birth_info['year_animal']}
        """
        
        # Format the bases information
        bases_text = "ค่าที่คำนวณได้จาก 7 ตัว 9 ฐาน:\n"
        for base_name, sequence in bases.items():
            if base_name in ["base1", "base2", "base3", "base4"]:  # Only include first 4 bases
                bases_text += f"- {base_name}: {sequence}\n"
        
        # Format the meanings
        meanings_text = "ความหมายที่เกี่ยวข้อง:\n"
        for meaning in meanings:
            meanings_text += f"- ฐานที่ {meaning['base']}, ตำแหน่งที่ {meaning['position']}: {meaning['heading']}\n"
            meanings_text += f"  {meaning['meaning']}\n\n"
        
        # Complete user prompt
        return f"""
        {birth_info_text}
        
        {bases_text}
        
        {meanings_text}
        
        คำถามของผู้ใช้: "{question}"
        
        กรุณาให้คำทำนายเกี่ยวกับคำถามของผู้ใช้ โดยใช้ข้อมูลจากเลข 7 ตัว 9 ฐาน ที่คำนวณได้ และความหมายที่ให้มา
        ตอบให้เหมือนหมอดูจริงๆ ที่มีความรู้ลึกซึ้งในศาสตร์นี้ แต่ไม่ต้องใช้คำทักทายหรือลงท้ายแบบตายตัว
        """
    
    async def generate_response(self, birth_info: Dict, bases: Dict, meanings: List[Dict], question: str, language="thai"):
        """Generate a fortune telling response using OpenAI"""
        system_prompt = self.generate_system_prompt(language)
        user_prompt = self.generate_user_prompt(birth_info, bases, meanings, question)
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return "ขออภัย มีข้อผิดพลาดในการทำนาย กรุณาลองใหม่อีกครั้ง"