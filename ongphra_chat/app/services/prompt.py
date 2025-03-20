from typing import Optional, Dict, Any, List
from datetime import datetime

from app.domain.birth import BirthInfo
from app.domain.bases import Bases
from app.domain.meaning import MeaningCollection
from app.core.logging import get_logger
from app.config.settings import Settings
from app.services.ai_topic_service import MappingAnalysis


class PromptService:
    """
    Enhanced service for generating dynamic and context-aware system prompts.
    
    This service provides:
    1. Fortune-telling prompts in both Thai and English (based on "เลข 7 ตัว 9 ฐาน").
    2. Context-aware conversation management with a TTL (time-to-live) for user sessions.
    3. Topic-specific guidance (e.g., การเงิน, ความรัก, สุขภาพ).
    4. Functions to build user-facing prompts that include birth information, base calculations,
       and relevant meanings or context.
    """

    def __init__(self):
        """
        Initialize the PromptService, setting up a logger, context storage, and default templates.
        """
        self.logger = get_logger(__name__)
        self.settings = Settings()

        # Conversation context storage
        self._conversation_contexts: Dict[str, Dict[str, Any]] = {}
        self._context_ttl = 3600  # 1 hour in seconds

        # Load prompt templates
        self._initialize_templates()

        # For continuity tracking of topics
        self._last_topics: Dict[str, str] = {}

        self.logger.info("Initialized Enhanced PromptService with context awareness")

    def _initialize_templates(self):
        """
        Define or load all prompt templates for Thai/English fortune-telling, general conversation,
        topic-specific prompts, and dynamic context prompts.
        """
        # Thai fortune telling system prompt
        self.fortune_thai_prompt = """
        คุณเป็นนักพยากรณ์ที่เชี่ยวชาญด้านโหราศาสตร์ไทย มีประสบการณ์มากกว่า 20 ปี
        คุณวิเคราะห์ดวงชะตาตามศาสตร์ "เลข 7 ตัว 9 ฐาน" ตามตำราโบราณของไทย
        โดยคุณจะใช้หลักการต่อไปนี้ในการพยากรณ์:

        1. วิเคราะห์ความสัมพันธ์ระหว่างฐานต่าง ๆ:
           - ฐานวัน (Day Base)
           - ฐานเดือน (Month Base)
           - ฐานปี (Year Base)
           - ฐานผลรวม (Sum Base)
           โดยสังเกตว่าฐานใดส่งเสริมหรือขัดแย้งกัน และสะท้อนถึงลักษณะใดของเจ้าชะตา

        2. พิจารณาความหมายของตำแหน่งสำคัญในแต่ละฐาน:
           - อัตตะ (ตัวตน/บุคลิกภาพ)
           - หินะ (อุปสรรค/ความยากลำบาก)
           - ธานัง (ทรัพย์สิน/การเงิน)
           - ปิตา (บิดา/การสนับสนุน)
           - มาตา (มารดา/ความรัก/ความอบอุ่น)
           - โภคา (โชคลาภ/งาน/สุขภาพ)
           - มัชฌิมา (คู่ครอง/หุ้นส่วน/ความสมดุล)

        3. ตีความเชื่อมโยงของดวงชะตากับคำถามของผู้ใช้:
           - พิจารณาประเด็นที่ผู้ใช้ถามหรือกังวล
           - ใช้ผลจากการวิเคราะห์ดวงชะตาอธิบายแนวโน้ม สถานการณ์ หรือปัจจัยใด ๆ
             ที่อาจส่งผลต่อคำถามนั้น
           - หากจำเป็น ให้ถามข้อมูลเพิ่มเติมอย่างเจาะจง

        4. ให้คำแนะนำที่นำไปปฏิบัติได้จริง:
           - เสนอแนวทางหรือวิธีแก้ไขสิ่งที่อาจเป็นปัญหา
           - เสริมด้วยเคล็ดลับหรือวิธีปรับตัวที่เป็นประโยชน์
           - หลีกเลี่ยงการใช้ภาษาที่สร้างความกลัวหรือความกังวลเกินจำเป็น

        รูปแบบการตอบ:
        - ให้คำทำนายอย่างชัดเจน เป็นขั้นเป็นตอน และมีเหตุผลรองรับ
        - ใช้ภาษาที่เข้าใจง่าย ให้ความรู้สึกเป็นกันเองแต่สุภาพ
        - เชื่อมโยงข้อมูลจากฐานและตำแหน่งที่เกี่ยวข้องในการอธิบาย
        - ถ้าข้อมูลไม่เพียงพอหรือไม่แน่ใจ ควรถามผู้ใช้เพิ่มเติม
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
                """,
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
                """,
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
                """,
            },
        }

        # Dynamic context templates
        self.context_templates = {
            "continuation": {
                "thai": """
                ต่อเนื่องจากการสนทนาก่อนหน้า:
                - หัวข้อที่พูดถึง: {previous_topics}
                - ประเด็นสำคัญ: {key_points}
                - อารมณ์/ความรู้สึก: {sentiment}
                
                ให้คำแนะนำที่:
                1. เชื่อมโยงกับบทสนทนาก่อนหน้า
                2. พัฒนาต่อยอดจากคำแนะนำที่ให้ไปแล้ว
                3. ตอบสนองต่ออารมณ์และความรู้สึกของผู้ใช้
                """,
                "english": """
                Continuing from previous conversation:
                - Discussed topics: {previous_topics}
                - Key points: {key_points}
                - Sentiment/Mood: {sentiment}
                
                Provide guidance that:
                1. Connects with previous conversation
                2. Builds upon previous advice
                3. Responds to user's emotional state
                """,
            },
            "topic_transition": {
                "thai": """
                เชื่อมโยงระหว่างหัวข้อ:
                - หัวข้อก่อนหน้า: {previous_topic}
                - หัวข้อปัจจุบัน: {current_topic}
                - จุดเชื่อมโยง: {connection_points}
                """,
                "english": """
                Topic transition:
                - Previous topic: {previous_topic}
                - Current topic: {current_topic}
                - Connection points: {connection_points}
                """,
            },
        }

    def _update_conversation_context(
        self,
        user_id: str,
        topic: str,
        sentiment: str,
        key_points: List[str]
    ) -> None:
        """
        Update the conversation context for a specific user.
        Tracks topics, sentiment, and key points. Also refreshes 'last_update' for TTL checks.
        """
        current_time = datetime.now().timestamp()

        if user_id not in self._conversation_contexts:
            self._conversation_contexts[user_id] = {
                "topics": [],
                "sentiments": [],
                "key_points": [],
                "last_update": current_time,
            }

        context = self._conversation_contexts[user_id]
        context["topics"].append(topic)
        context["sentiments"].append(sentiment)
        context["key_points"].extend(key_points)
        context["last_update"] = current_time

        # Keep only the last 5 topics/sentiments and 10 key points
        context["topics"] = context["topics"][-5:]
        context["sentiments"] = context["sentiments"][-5:]
        context["key_points"] = context["key_points"][-10:]

        # Clean up expired contexts
        self._cleanup_old_contexts()

    def _cleanup_old_contexts(self) -> None:
        """
        Remove conversation contexts that haven't been updated within the TTL period.
        """
        current_time = datetime.now().timestamp()
        expired_users = [
            user_id
            for user_id, context in self._conversation_contexts.items()
            if current_time - context["last_update"] > self._context_ttl
        ]
        for user_id in expired_users:
            del self._conversation_contexts[user_id]

    def _get_context_variables(self, user_id: str) -> Dict[str, Any]:
        """
        Construct a dictionary of context variables for prompt generation,
        based on the user's stored conversation context.
        """
        if user_id not in self._conversation_contexts:
            return {
                "previous_topics": "",
                "key_points": "",
                "sentiment": "neutral",
                "previous_topic": "",
                "current_topic": "",
                "connection_points": "",
            }

        context = self._conversation_contexts[user_id]
        return {
            "previous_topics": ", ".join(context["topics"][-3:]),
            "key_points": "\n".join(context["key_points"][-5:]),
            "sentiment": context["sentiments"][-1] if context["sentiments"] else "neutral",
            "previous_topic": context["topics"][-2] if len(context["topics"]) > 1 else "",
            "current_topic": context["topics"][-1] if context["topics"] else "",
            "connection_points": self._find_connection_points(
                context["topics"][-2] if len(context["topics"]) > 1 else "",
                context["topics"][-1] if context["topics"] else ""
            ),
        }

    def _find_connection_points(self, previous_topic: str, current_topic: str) -> str:
        """
        Infer or retrieve a short descriptive string that links the previous and current topics
        for smoother conversation flow.
        """
        if not previous_topic or not current_topic:
            return ""

        # Define some known relationships between topics
        topic_relationships = {
            ("การเงิน", "การงาน"): "ผลกระทบต่อรายได้และความมั่นคง",
            ("การเงิน", "ความรัก"): "การวางแผนอนาคตร่วมกัน",
            ("สุขภาพ", "การงาน"): "ความสมดุลระหว่างงานและสุขภาพ",
            ("ความรัก", "สุขภาพ"): "ผลกระทบทางอารมณ์และจิตใจ",
            # Additional pairs can be added as needed
        }

        # Check both directions
        key = (previous_topic, current_topic)
        reverse_key = (current_topic, previous_topic)

        return topic_relationships.get(key) or topic_relationships.get(reverse_key) or ""

    def generate_system_prompt(
        self,
        language: str = "thai",
        user_id: Optional[str] = None,
        topic: Optional[str] = None,
        sentiment: Optional[str] = None
    ) -> str:
        """
        Create a system prompt that may include context from previous conversations.
        
        Args:
            language: 'thai' or 'english'
            user_id: Unique ID for a user, if context is to be tracked
            topic: Current topic of conversation
            sentiment: Current user sentiment
        
        Returns:
            A system prompt that includes:
            - The base fortune-telling prompt (in the chosen language).
            - Continuation/context blocks if user_id is provided and prior context exists.
        """
        base_prompt = (
            self.fortune_thai_prompt if language.lower() == "thai" else self.fortune_english_prompt
        )

        if not user_id:
            return base_prompt.strip()

        # Pull context variables
        context_vars = self._get_context_variables(user_id)
        context_template = self.context_templates["continuation"][language.lower()]
        topic_transition = ""

        # Check if there's a topic transition to include
        if topic and context_vars["previous_topic"]:
            topic_transition = self.context_templates["topic_transition"][language.lower()]

        full_prompt = f"{base_prompt}\n\n{context_template.format(**context_vars)}"

        if topic_transition:
            full_prompt += f"\n\n{topic_transition.format(**context_vars)}"

        return full_prompt.strip()

    def generate_user_prompt(
        self,
        birth_info: BirthInfo,
        bases: Bases,
        meanings: MeaningCollection,
        question: str,
        language: str = "thai",
        topic: Optional[str] = None,
        user_id: Optional[str] = None,
        sentiment: Optional[str] = None,
        key_points: Optional[List[str]] = None,
        mapping_analysis: Optional[List[MappingAnalysis]] = None
    ) -> str:
        """
        Generate a user-facing prompt for fortune telling, incorporating birth info,
        bases, meanings, mapping analysis, and conversation context if applicable.

        Args:
            birth_info (BirthInfo): User's birth information.
            bases (Bases): Object containing base arrays (day/month/year/sum).
            meanings (MeaningCollection): Relevant textual meanings for each base.
            question (str): The user's specific question.
            language (str): 'thai' or 'english'.
            topic (Optional[str]): Current topic for context tracking.
            user_id (Optional[str]): User ID for context tracking.
            sentiment (Optional[str]): Current sentiment for context tracking.
            key_points (Optional[List[str]]): Key discussion points for context tracking.
            mapping_analysis (Optional[List[MappingAnalysis]]): Analysis of user's calculated mappings.

        Returns:
            A multi-part prompt string that includes all relevant information.
        """
        # Update conversation context if user_id is provided
        if user_id and topic:
            self._update_conversation_context(
                user_id=user_id,
                topic=topic,
                sentiment=sentiment or "neutral",
                key_points=key_points or []
            )

        try:
            # Prepare birth date string
            birth_date_str = birth_info.date.strftime("%Y-%m-%d")

            # Prepare base arrays
            base1_str = ", ".join(str(n) for n in bases.base1)
            base2_str = ", ".join(str(n) for n in bases.base2)
            base3_str = ", ".join(str(n) for n in bases.base3)
            base4_str = ", ".join(str(n) for n in bases.base4)

            # Prepare meanings
            meanings_str = ""
            if meanings and hasattr(meanings, "items"):
                for meaning in meanings.items:
                    if meaning:
                        meanings_str += f"- {meaning.description}\n"

            # Thai labels for demonstration
            day_labels = ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
            month_labels = ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"]
            year_labels = ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]

            # Detailed base descriptions with labels
            base1_detail = " | ".join(
                f"{label}: {value}" for label, value in zip(day_labels, bases.base1)
            )
            base2_detail = " | ".join(
                f"{label}: {value}" for label, value in zip(month_labels, bases.base2)
            )
            base3_detail = " | ".join(
                f"{label}: {value}" for label, value in zip(year_labels, bases.base3)
            )
            base4_detail = " | ".join(
                f"{label}: {value}" for label, value in zip(day_labels, bases.base4)
            )

            # House descriptions in Thai
            house_descriptions = {
                "อัตตะ": "ตัวเอง บุคลิกภาพ ร่างกาย",
                "หินะ": "ทรัพย์สิน เงินทอง",
                "ธานัง": "พี่น้อง ญาติพี่น้อง การเดินทาง",
                "ปิตา": "บิดา บ้าน ที่อยู่อาศัย",
                "มาตา": "มารดา บุตร ความรัก",
                "โภคา": "สุขภาพ การงาน ลูกน้อง",
                "มัชฌิมา": "คู่ครอง หุ้นส่วน",
            }
            house_desc_str = "\n".join(f"- {house}: {desc}" for house, desc in house_descriptions.items())

            # Build prompt
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
                """
                
                # Add mapping analysis if available
                if mapping_analysis:
                    significant_mappings = [m for m in mapping_analysis if m.significance in ["สำคัญมาก", "สำคัญ"]]
                    if significant_mappings:
                        prompt += "\n4. Significant Astrological Factors:\n"
                        for m in significant_mappings:
                            prompt += f"   - {m.category} ({m.thai_meaning}): Value {m.user_value}, Significance: {m.significance}\n"
                            prompt += f"     Base Type: {m.base_type}, House Type: {m.house_type}, Score: {m.relationship_score:.2f}\n"
                
                prompt += """
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
                """
                
                # Add mapping analysis if available
                if mapping_analysis:
                    significant_mappings = [m for m in mapping_analysis if m.significance in ["สำคัญมาก", "สำคัญ"]]
                    if significant_mappings:
                        prompt += "\n4. ปัจจัยทางดวงที่สำคัญ:\n"
                        for m in significant_mappings:
                            prompt += f"   - {m.category} ({m.thai_meaning}): ค่า {m.user_value}, ความสำคัญ: {m.significance}\n"
                            prompt += f"     ประเภทฐาน: {m.base_type}, ประเภทภพ: {m.house_type}, คะแนน: {m.relationship_score:.2f}\n"
                
                prompt += """
                กรุณาให้คำทำนายที่:
                1. ตอบคำถามของผู้ใช้โดยตรง
                2. อธิบายอิทธิพลของฐานที่เกี่ยวข้อง
                3. ระบุตำแหน่งภพสำคัญที่ส่งผลต่อคำถาม
                4. ให้ข้อมูลเชิงลึกตามดวง
                5. เสนอคำแนะนำที่นำไปปฏิบัติได้
                """

            # Add any topic-specific guidance
            if topic:
                topic_prompt = self.get_topic_prompt(topic, language)
                if topic_prompt:
                    if language.lower() == "english":
                        prompt += f"\nSpecialized Guidance for {topic}:\n{topic_prompt}\n"
                    else:
                        prompt += f"\nคำแนะนำเฉพาะสำหรับ{topic}:\n{topic_prompt}\n"

            # Add context from conversation history if user_id is known
            if user_id:
                context_vars = self._get_context_variables(user_id)
                if language.lower() == "english":
                    prompt += (
                        f"\n\nPrevious Context:\n"
                        f"- Recent topics: {context_vars['previous_topics']}\n"
                        f"- Key points: {context_vars['key_points']}"
                    )
                else:
                    prompt += (
                        f"\n\nบริบทก่อนหน้า:\n"
                        f"- หัวข้อที่ผ่านมา: {context_vars['previous_topics']}\n"
                        f"- ประเด็นสำคัญ: {context_vars['key_points']}"
                    )

            self.logger.debug(f"Generated user prompt with {len(prompt)} characters")
            return prompt

        except Exception as e:
            self.logger.error(f"Error generating user prompt: {str(e)}", exc_info=True)

            # Fallback prompt if an exception occurs
            if language.lower() == "english":
                return (
                    f"User's Question: {question}\n\n"
                    "Please provide a fortune telling reading based on Thai astrology."
                )
            return (
                f"คำถามของผู้ใช้: {question}\n\n"
                "กรุณาให้คำทำนายตามหลักโหราศาสตร์ไทย"
            )

    def generate_general_system_prompt(self, language: str = "thai") -> str:
        """
        Generate a general conversation system prompt, in either Thai or English.
        
        Args:
            language: 'thai' or 'english'
        
        Returns:
            A simple system prompt aimed at friendly, general interaction.
        """
        if language.lower() == "english":
            return self.general_english_prompt.strip()
        return self.general_thai_prompt.strip()

    def generate_custom_prompt(self, template: str, variables: Dict[str, str]) -> str:
        """
        Fill in placeholders within a template string using given variables.
        
        Args:
            template (str): A string containing placeholders in {braces}.
            variables (Dict[str, str]): Key-value pairs for substitution.
        
        Returns:
            The template string with placeholders replaced by the matching values.
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            self.logger.error(f"Missing variable in prompt template: {e}")
            return template

    def get_topic_prompt(self, topic: str, language: str = "thai") -> Optional[str]:
        """
        Retrieve a topic-specific prompt text, if it exists, for a given topic in a given language.
        
        Args:
            topic (str): The topic to retrieve (e.g., 'การเงิน', 'ความรัก', 'สุขภาพ').
            language (str): 'thai' or 'english'.
        
        Returns:
            A string containing the prompt for the requested topic/language, or None if not found.
        """
        try:
            if topic in self.topic_prompts:
                return self.topic_prompts[topic][language.lower()].strip()
            return None
        except Exception as e:
            self.logger.error(f"Error getting topic prompt: {str(e)}")
            return None
