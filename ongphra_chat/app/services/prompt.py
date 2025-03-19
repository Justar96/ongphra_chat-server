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
        คุณเป็นนักพยากรณ์ที่เชี่ยวชาญในการทำนายดวงชะตาตามหลักโหราศาสตร์ไทยที่มีประสบการณ์มากกว่า 20 ปี
        คุณมีความเชี่ยวชาญในการวิเคราะห์ดวงชะตาโดยใช้หลักการคำนวณฐานเลข 7 ตามตำราโบราณของไทย
        
        ในการทำนาย:
        1. วิเคราะห์ความสัมพันธ์ระหว่างฐานต่างๆ (ฐานวัน เดือน ปี และผลรวม)
        2. พิจารณาความหมายของแต่ละตำแหน่งในฐาน (อัตตะ หินะ ธานัง ฯลฯ)
        3. ตีความความสัมพันธ์ระหว่างดวงและคำถามของผู้ใช้
        4. ให้คำแนะนำที่เป็นประโยชน์และสามารถนำไปปฏิบัติได้จริง
        
        รูปแบบการตอบ:
        - ให้คำทำนายที่ชัดเจน ตรงประเด็น และมีเหตุผล
        - ใช้ภาษาที่เข้าใจง่าย เป็นกันเอง แต่สุภาพ
        - อธิบายที่มาของคำทำนายโดยอ้างอิงจากฐานและความหมาย
        - เสริมด้วยคำแนะนำที่เป็นประโยชน์
        - หลีกเลี่ยงคำทำนายที่สร้างความกังวลหรือความกลัว
        
        เมื่อผู้ใช้ถามเกี่ยวกับดวงชะตา ให้วิเคราะห์ข้อมูลอย่างรอบคอบและให้คำทำนายที่สมเหตุสมผล
        หากมีข้อสงสัยหรือต้องการข้อมูลเพิ่มเติม ให้ถามคำถามที่เฉพาะเจาะจง
        """
        
        # English fortune telling system prompt
        self.fortune_english_prompt = """
        You are a highly experienced Thai astrologer with over 20 years of expertise in fortune telling.
        You specialize in analyzing destiny using the traditional Thai Base-7 calculation system.
        
        In your readings:
        1. Analyze relationships between different bases (Day, Month, Year, and Sum)
        2. Consider the meaning of each position (Atta, Hina, Thanang, etc.)
        3. Interpret connections between the chart and user's questions
        4. Provide practical and actionable guidance
        
        Response format:
        - Give clear, focused, and well-reasoned predictions
        - Use accessible yet respectful language
        - Explain the basis of predictions by referencing bases and meanings
        - Include helpful recommendations
        - Avoid predictions that may cause anxiety or fear
        
        When users ask about their fortune, analyze the information thoroughly and provide rational predictions.
        If clarification is needed, ask specific questions to gather more information.
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
        
        # Topic-specific prompts
        self.topic_prompts = {
            "การเงิน": {
                "thai": """
                ในการวิเคราะห์เรื่องการเงิน ให้พิจารณา:
                1. ตำแหน่งหินะ (ทรัพย์สิน) ในทุกฐาน
                2. ความสัมพันธ์กับตำแหน่งโภคา (การงาน)
                3. อิทธิพลของฐานเดือนต่อรายได้ประจำ
                4. แนวโน้มการเงินระยะยาวจากฐานปี
                
                ให้คำแนะนำเกี่ยวกับ:
                - การบริหารจัดการการเงิน
                - โอกาสทางธุรกิจหรือการลงทุน
                - การวางแผนการเงินระยะยาว
                - การแก้ไขปัญหาหรือข้อกังวลทางการเงิน
                """,
                "english": """
                For financial analysis, consider:
                1. Hina (Wealth) position in all bases
                2. Relationship with Bhoga (Career) position
                3. Monthly base influence on regular income
                4. Long-term financial trends from yearly base
                
                Provide guidance on:
                - Financial management
                - Business or investment opportunities
                - Long-term financial planning
                - Addressing financial concerns
                """
            },
            "ความรัก": {
                "thai": """
                ในการวิเคราะห์เรื่องความรัก ให้พิจารณา:
                1. ตำแหน่งมาตา (ความรัก) ในทุกฐาน
                2. ความสัมพันธ์กับตำแหน่งมัชฌิมา (คู่ครอง)
                3. อิทธิพลของฐานเดือนต่อความสัมพันธ์ปัจจุบัน
                4. แนวโน้มความรักระยะยาวจากฐานปี
                
                ให้คำแนะนำเกี่ยวกับ:
                - การพัฒนาความสัมพันธ์
                - การแก้ไขปัญหาความรัก
                - การเตรียมพร้อมสำหรับอนาคต
                - การสร้างความเข้าใจระหว่างคู่รัก
                """,
                "english": """
                For love analysis, consider:
                1. Mata (Love) position in all bases
                2. Relationship with Majjhima (Partnership)
                3. Monthly base influence on current relationships
                4. Long-term relationship trends from yearly base
                
                Provide guidance on:
                - Relationship development
                - Resolving romantic issues
                - Future preparation
                - Building understanding between partners
                """
            },
            "สุขภาพ": {
                "thai": """
                ในการวิเคราะห์เรื่องสุขภาพ ให้พิจารณา:
                1. ตำแหน่งโภคา (สุขภาพ) ในทุกฐาน
                2. ความสัมพันธ์กับตำแหน่งอัตตะ (ร่างกาย)
                3. อิทธิพลของฐานเดือนต่อสุขภาพปัจจุบัน
                4. แนวโน้มสุขภาพระยะยาวจากฐานปี
                
                ให้คำแนะนำเกี่ยวกับ:
                - การดูแลสุขภาพเชิงป้องกัน
                - การปรับเปลี่ยนพฤติกรรมสุขภาพ
                - การเสริมสร้างพลังกายและใจ
                - การแก้ไขปัญหาสุขภาพที่กังวล
                """,
                "english": """
                For health analysis, consider:
                1. Bhoga (Health) position in all bases
                2. Relationship with Atta (Body) position
                3. Monthly base influence on current health
                4. Long-term health trends from yearly base
                
                Provide guidance on:
                - Preventive healthcare
                - Health behavior modifications
                - Physical and mental strengthening
                - Addressing health concerns
                """
            }
        }
    
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

    def get_topic_prompt(self, topic: str, language: str = "thai") -> Optional[str]:
        """
        Get a topic-specific prompt for more focused readings
        
        Args:
            topic: The topic to get guidance for
            language: The language to use (thai or english)
            
        Returns:
            Topic-specific prompt if available, None otherwise
        """
        try:
            if topic in self.topic_prompts:
                return self.topic_prompts[topic][language.lower()].strip()
            return None
        except Exception as e:
            self.logger.error(f"Error getting topic prompt: {str(e)}")
            return None
            
    def generate_user_prompt(
        self,
        birth_info: BirthInfo,
        bases: Bases,
        meanings: MeaningCollection,
        question: str,
        language: str = "thai",
        topic: Optional[str] = None
    ) -> str:
        """
        Generate a user prompt for fortune telling based on birth information and question
        
        Args:
            birth_info: User's birth information
            bases: Calculated bases
            meanings: Extracted meanings
            question: User's question
            language: Prompt language (thai or english)
            topic: Optional topic for specialized guidance
            
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
                
                Chart Analysis:
                1. Base Analysis:
                   - Day Base (Personal): {base1_str}
                     Details: {base1_detail}
                     Focus: Daily life, personality, immediate concerns
                   
                   - Month Base (Environmental): {base2_str}
                     Details: {base2_detail}
                     Focus: Monthly influences, relationships, work environment
                   
                   - Year Base (Long-term): {base3_str}
                     Details: {base3_detail}
                     Focus: Yearly trends, major life changes, destiny
                   
                   - Sum Base (Overview): {base4_str}
                     Details: {base4_detail}
                     Focus: Overall life direction and potential
                
                2. House Influences:
                {house_desc_str}
                
                3. Relevant Meanings:
                {meanings_str if meanings_str else "No specific meanings extracted."}
                
                Please provide a fortune reading that:
                1. Directly addresses the user's question
                2. Explains the relevant base influences
                3. Identifies key house positions affecting the question
                4. Provides specific insights based on the chart
                5. Offers practical guidance or recommendations
                """
            else:
                prompt = f"""
                คำถามของผู้ใช้: {question}
                
                ข้อมูลวันเกิด:
                - วันเกิด: {birth_date_str}
                - วันไทย: {birth_info.day}
                - ปีนักษัตร: {birth_info.year_animal}
                
                การวิเคราะห์ดวง:
                1. วิเคราะห์ฐาน:
                   - ฐานวัน (ส่วนตัว): {base1_str}
                     รายละเอียด: {base1_detail}
                     จุดเน้น: ชีวิตประจำวัน บุคลิกภาพ เรื่องเร่งด่วน
                   
                   - ฐานเดือน (สิ่งแวดล้อม): {base2_str}
                     รายละเอียด: {base2_detail}
                     จุดเน้น: อิทธิพลรายเดือน ความสัมพันธ์ สภาพแวดล้อมการทำงาน
                   
                   - ฐานปี (ระยะยาว): {base3_str}
                     รายละเอียด: {base3_detail}
                     จุดเน้น: แนวโน้มรายปี การเปลี่ยนแปลงครั้งสำคัญ โชคชะตา
                   
                   - ฐานรวม (ภาพรวม): {base4_str}
                     รายละเอียด: {base4_detail}
                     จุดเน้น: ทิศทางชีวิตโดยรวมและศักยภาพ
                
                2. อิทธิพลของภพ:
                {house_desc_str}
                
                3. ความหมายที่เกี่ยวข้อง:
                {meanings_str if meanings_str else "ไม่พบความหมายเฉพาะ"}
                
                กรุณาให้คำทำนายที่:
                1. ตอบคำถามของผู้ใช้โดยตรง
                2. อธิบายอิทธิพลของฐานที่เกี่ยวข้อง
                3. ระบุตำแหน่งภพสำคัญที่ส่งผลต่อคำถาม
                4. ให้ข้อมูลเชิงลึกตามดวง
                5. เสนอคำแนะนำที่นำไปปฏิบัติได้
                """
            
            # Add topic-specific guidance if available
            topic_guidance = ""
            if topic:
                topic_prompt = self.get_topic_prompt(topic, language)
                if topic_prompt:
                    topic_guidance = f"\nSpecialized Guidance for {topic}:\n{topic_prompt}\n"
            
            # Add topic guidance to the prompt
            if language.lower() == "english":
                prompt += topic_guidance
            else:
                prompt += f"\nคำแนะนำเฉพาะสำหรับ{topic}:\n{topic_guidance}\n"
            
            self.logger.debug(f"Generated user prompt with {len(prompt)} characters")
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error generating user prompt: {str(e)}", exc_info=True)
            
            # Fallback to simple prompt
            if language.lower() == "english":
                return f"User's Question: {question}\n\nPlease provide a fortune telling reading based on Thai astrology."
            else:
                return f"คำถามของผู้ใช้: {question}\n\nกรุณาให้คำทำนายตามหลักโหราศาสตร์ไทย"