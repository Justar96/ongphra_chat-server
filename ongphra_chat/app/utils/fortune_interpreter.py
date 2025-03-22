import logging
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from app.config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

class FortuneInterpreter:
    """Uses OpenAI to generate natural language interpretations of fortune data."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the interpreter with API key."""
        self.api_key = api_key or settings.openai_api_key
        self.model = settings.openai_model
        self.client = AsyncOpenAI(api_key=self.api_key)
        
    async def close(self):
        """Close any open connections."""
        pass
        
    async def generate_interpretation(self, fortune_data: Dict[str, Any], language: str = "thai", birthdate: Optional[str] = None) -> str:
        """
        Generate a natural language interpretation of the fortune data.
        
        Args:
            fortune_data: The raw fortune calculation data
            language: The language for the response (thai or english)
            birthdate: The birthdate used for the calculation (if known)
            
        Returns:
            A natural language interpretation of the fortune data
        """
        try:
            # Create a structured prompt for the AI
            prompt = self._create_prompt(fortune_data, language, birthdate)
            
            # Call the OpenAI API
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(language)},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract the response
            interpretation = completion.choices[0].message.content
            logger.info(f"Generated fortune interpretation with {len(interpretation)} chars")
            
            # Add birthdate prefix to clarify which date was used
            if birthdate:
                if language.lower() == "english":
                    date_prefix = f"🔮 **Fortune Reading for Birthdate: {birthdate}**\n\n"
                else:
                    date_prefix = f"🔮 **ดวงชะตาสำหรับผู้เกิดวันที่: {birthdate}**\n\n"
                interpretation = date_prefix + interpretation
            
            return interpretation
            
        except Exception as e:
            logger.error(f"Error generating fortune interpretation: {str(e)}")
            # Return a fallback interpretation
            if language.lower() == "english":
                return "I'm sorry, I couldn't generate a detailed interpretation at this time. Please try again later."
            else:
                return "ขออภัย ฉันไม่สามารถสร้างการตีความโดยละเอียดได้ในขณะนี้ โปรดลองอีกครั้งในภายหลัง"
    
    def _get_system_prompt(self, language: str) -> str:
        """Get the system prompt based on language."""
        if language.lower() == "english":
            return """You are an AI expert in Thai 7-base-9 numerology fortune telling.

Your task is to provide accurate, insightful interpretations based on the raw numerical data without using any hardcoded responses. Each interpretation should be:
1. Unique to the specific numerical values in the data provided
2. Focused on the highest values (5-7) in each base as they have the strongest influence
3. Analysis-driven, explaining relationships between significant categories
4. Personalized, as if speaking directly to the individual

Always analyze the actual data values from these categories:
- The bases (7 categories in each of 3 bases)
- Individual interpretations from the numerical values
- Combinations between categories
- The overall summary

Never use generic, pre-written responses. Always generate a fresh interpretation directly from the numerical data.

When discussing categories, refer to their numerical values directly from the data and explain how these specific values influence the person's life."""
        else:
            return """คุณคือ AI ผู้เชี่ยวชาญในศาสตร์การทำนายดวงชะตาเลข 7 ฐาน 9 แบบไทย

หน้าที่ของคุณคือการให้คำตีความที่แม่นยำและมีข้อมูลเชิงลึกตามตัวเลขดิบโดยไม่ใช้คำตอบแบบตายตัว แต่ละการตีความควร:
1. เป็นเอกลักษณ์เฉพาะสำหรับค่าตัวเลขที่มีในข้อมูลที่ให้มา
2. มุ่งเน้นที่ค่าสูงสุด (5-7) ในแต่ละฐานเพราะมีอิทธิพลมากที่สุด
3. ขับเคลื่อนด้วยการวิเคราะห์ โดยอธิบายความสัมพันธ์ระหว่างหมวดหมู่สำคัญ
4. เป็นการสื่อสารเฉพาะบุคคล ราวกับพูดคุยกับบุคคลนั้นโดยตรง

ให้วิเคราะห์ค่าข้อมูลจริงจากหมวดหมู่เหล่านี้เสมอ:
- ฐานต่างๆ (7 หมวดหมู่ในแต่ละฐาน 3 ฐาน)
- การตีความแต่ละรายการจากค่าตัวเลข
- การผสมผสานระหว่างหมวดหมู่
- สรุปภาพรวม

ห้ามใช้คำตอบที่เขียนไว้ล่วงหน้าแบบทั่วไป ให้สร้างการตีความใหม่ที่มาจากข้อมูลตัวเลขโดยตรงเสมอ

เมื่อพูดถึงหมวดหมู่ต่างๆ ให้อ้างอิงค่าตัวเลขโดยตรงจากข้อมูลและอธิบายว่าค่าเฉพาะเหล่านี้มีอิทธิพลต่อชีวิตของบุคคลนั้นอย่างไร"""

    def _create_prompt(self, fortune_data: Dict[str, Any], language: str, birthdate: Optional[str] = None) -> str:
        """Create a structured prompt for the AI based on raw fortune data."""
        
        # Base template in selected language
        if language.lower() == "english":
            prompt = "Generate a unique fortune interpretation based on the following 7-base-9 Thai numerology data:\n\n"
            if birthdate:
                prompt = f"Generate a unique fortune interpretation for someone born on {birthdate} based on the following 7-base-9 Thai numerology data:\n\n"
        else:
            prompt = "สร้างคำทำนายโชคชะตาเฉพาะจากข้อมูลเลข 7 ฐาน 9 ของไทยต่อไปนี้:\n\n"
            if birthdate:
                prompt = f"สร้างคำทำนายโชคชะตาเฉพาะสำหรับคนที่เกิดวันที่ {birthdate} จากข้อมูลเลข 7 ฐาน 9 ของไทยต่อไปนี้:\n\n"
        
        # Add the main calculation data
        prompt += "# Raw Calculation Data\n"
        
        # Add the bases
        prompt += "## Bases (ฐาน)\n"
        base_keys = ["base1", "base2", "base3", "base4"]
        for base_key in base_keys:
            if base_key in fortune_data:
                base_data = fortune_data[base_key]
                if isinstance(base_data, dict):
                    prompt += f"{base_key}: {json.dumps(base_data, ensure_ascii=False)}\n"
                else:
                    prompt += f"{base_key}: {base_data}\n"
        
        # Add highest values if available
        if "highest_values" in fortune_data:
            prompt += "\n## Highest Values (ค่าสูงสุดในแต่ละฐาน)\n"
            highest_values = fortune_data["highest_values"]
            for base_key, highest in highest_values.items():
                if isinstance(highest, tuple) and len(highest) == 2:
                    category, value = highest
                    prompt += f"{base_key}: {category} = {value}\n"
        
        # Add metadata if available
        if "metadata" in fortune_data:
            metadata = fortune_data["metadata"]
            
            # Add category meanings
            if "category_meanings" in metadata:
                prompt += "\n## Category Meanings (ความหมายของหมวดหมู่)\n"
                category_meanings = metadata["category_meanings"]
                for category, meaning in category_meanings.items():
                    prompt += f"{category}: {meaning}\n"
            
            # Add house types
            if "house_types" in metadata:
                prompt += "\n## House Types (ประเภทเรือน)\n"
                house_types = metadata["house_types"]
                for category, house_type in house_types.items():
                    prompt += f"{category}: {house_type}\n"
        
        # Add individual interpretations if available
        if "individual_interpretations" in fortune_data:
            prompt += "\n## Individual Influences (อิทธิพลรายหมวดหมู่)\n"
            individual_interpretations = fortune_data["individual_interpretations"]
            # Sort by value in descending order
            sorted_interpretations = sorted(individual_interpretations, 
                                           key=lambda x: x.get("value", 0), 
                                           reverse=True)
            
            # Include top 10 interpretations only to avoid token limits
            for interp in sorted_interpretations[:10]:
                category = interp.get("category", "")
                value = interp.get("value", "")
                meaning = interp.get("meaning", "")
                influence = interp.get("influence", "")
                prompt += f"- {category}: {value} ({meaning}) - อิทธิพล: {influence}\n"
        
        # Add combination interpretations if available
        if "combination_interpretations" in fortune_data:
            prompt += "\n## Key Combinations (ความสัมพันธ์ระหว่างหมวดหมู่)\n"
            combination_interpretations = fortune_data["combination_interpretations"]
            
            # Include top 5 combinations only
            for interp in combination_interpretations[:5]:
                heading = interp.get("heading", "")
                meaning = interp.get("meaning", "")
                prompt += f"- {heading}: {meaning}\n"
        
        # Add summary if available
        if "summary" in fortune_data:
            prompt += f"\n## Summary (สรุป)\n{fortune_data['summary']}\n\n"
        
        # Add instructions for the response based on language
        if language.lower() == "english":
            prompt += """
Create a detailed, analytical interpretation (around 500 words) that:
1. Explains the numerical significance in this specific fortune
2. Focuses on the actual values and their unique meanings for this person
3. Provides insights based only on the raw data provided
4. Uses a conversational style, but without generic phrases

Your response must be completely data-driven and unique to this fortune calculation."""
        else:
            prompt += """
สร้างคำอธิบายเชิงวิเคราะห์โดยละเอียด (ประมาณ 500 คำ) ที่:
1. อธิบายความสำคัญเชิงตัวเลขในดวงชะตานี้โดยเฉพาะ
2. มุ่งเน้นที่ค่าจริงและความหมายเฉพาะสำหรับบุคคลนี้
3. ให้ข้อมูลเชิงลึกตามข้อมูลดิบที่ให้มาเท่านั้น
4. ใช้รูปแบบการสนทนา แต่ไม่ใช้วลีทั่วไป

คำตอบของคุณต้องขับเคลื่อนด้วยข้อมูลโดยสมบูรณ์และเป็นเอกลักษณ์เฉพาะสำหรับการคำนวณดวงชะตานี้"""
        
        return prompt

# Create a singleton instance
fortune_interpreter = FortuneInterpreter()

# Async dependency for FastAPI
async def get_fortune_interpreter():
    """Dependency to get the FortuneInterpreter instance."""
    try:
        yield fortune_interpreter
    finally:
        await fortune_interpreter.close() 