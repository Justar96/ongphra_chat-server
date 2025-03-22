from typing import Dict, List, Any, Callable, Optional, Union
import re
import json
import logging
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

# Import fortune calculator at the end of imports to avoid circular imports
try:
    from app.utils.fortune_calculator import calculate_fortune, enrich_fortune_calculation
except ImportError:
    logger.warning("Fortune calculator not available, fortune tools will not function correctly")
    
    # Create dummy functions for testing when the real ones aren't available
    def calculate_fortune(date_str):
        return {"bases": {"base1": {}, "base2": {}, "base3": {}}}
    
    def enrich_fortune_calculation(fortune_data, db_config=None):
        return fortune_data

class ToolFunction(BaseModel):
    """Definition of a tool function that can process specific message contexts"""
    name: str
    description: str
    pattern: Optional[str] = None
    prefix: Optional[str] = None
    
    def matches(self, message: str) -> bool:
        """Check if this tool should handle the given message"""
        if self.prefix and message.strip().startswith(self.prefix):
            return True
        if self.pattern and re.search(self.pattern, message, re.IGNORECASE):
            return True
        return False

class ToolResult(BaseModel):
    """Result from a tool function execution"""
    success: bool = True
    response: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    handled: bool = False  # Whether this tool fully handled the message
    modified_message: Optional[str] = None  # If the tool wants to modify but not fully handle the message

class ToolHandler:
    """Handler for processing message contexts with registered tools"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_definitions: Dict[str, ToolFunction] = {}
    
    def register(self, tool_def: ToolFunction):
        """Register a tool function"""
        def decorator(func: Callable):
            self.tools[tool_def.name] = func
            self.tool_definitions[tool_def.name] = tool_def
            return func
        return decorator
    
    async def process(self, message: str, user_id: Optional[str] = None, session_id: Optional[str] = None, **kwargs) -> ToolResult:
        """
        Process a message with the appropriate tool
        
        Args:
            message: The user message to process
            user_id: Optional user identifier
            session_id: Optional session identifier
            kwargs: Additional arguments to pass to the tool function
            
        Returns:
            ToolResult with the processing result
        """
        original_message = message
        
        # Check for JSON message format which might contain special directives
        try:
            if message.strip().startswith('{') and message.strip().endswith('}'):
                data = json.loads(message)
                if "command" in data or "tool" in data:
                    command = data.get("command") or data.get("tool")
                    if command in self.tools:
                        logger.info(f"Processing message with tool: {command}")
                        return await self.tools[command](data, user_id, session_id, **kwargs)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Check each tool's patterns
        for name, tool_def in self.tool_definitions.items():
            if tool_def.matches(message):
                logger.info(f"Message matched tool: {name}")
                if self.tools.get(name):
                    return await self.tools[name](message, user_id, session_id, **kwargs)
        
        # No tool matched
        return ToolResult(
            success=True,
            handled=False,
            modified_message=original_message
        )

# Create a global instance of the tool handler
tool_handler = ToolHandler()


# Example tool functions

@tool_handler.register(ToolFunction(
    name="fortune",
    description="Process fortune telling requests",
    pattern=r"\b(ดูดวง|fortune|horoscope|zodiac)\b"
))
async def process_fortune(message, user_id=None, session_id=None, **kwargs):
    """Process a fortune-telling request"""
    # This is just an example - implement the actual logic
    return ToolResult(
        success=True,
        handled=True,
        response="I can tell your fortune! Please provide your birthdate in YYYY-MM-DD format.",
        data={"context": "fortune_request"}
    )

@tool_handler.register(ToolFunction(
    name="birthdate",
    description="Extract birthdate information",
    pattern=r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b"
))
async def process_birthdate(message, user_id=None, session_id=None, **kwargs):
    """Process a message containing a birthdate"""
    # Extract the birthdate using regex
    match = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", message)
    if not match:
        return ToolResult(
            success=False,
            handled=False,
            error="Could not parse birthdate"
        )
    
    year, month, day = match.groups()
    
    # This is where you'd call your fortune calculation service
    # For now, we just return a simple response
    return ToolResult(
        success=True,
        handled=True,
        response=f"Thank you for providing your birthdate: {year}-{month}-{day}. I'll calculate your fortune now.",
        data={
            "context": "birthdate_provided",
            "birthdate": f"{year}-{month}-{day}"
        }
    )

@tool_handler.register(ToolFunction(
    name="image_generation",
    description="Handle image generation requests",
    pattern=r"\b(generate|create|draw|paint|show me)\s+.*(image|picture|drawing|art)\b"
))
async def process_image_generation(message, user_id=None, session_id=None, **kwargs):
    """Process an image generation request"""
    # This is just an example
    return ToolResult(
        success=True,
        handled=True,
        response="I can generate an image for you. Please describe what you'd like to see.",
        data={"context": "image_generation"}
    )

@tool_handler.register(ToolFunction(
    name="help",
    description="Provide help information",
    pattern=r"\b(help|ช่วยเหลือ|คำสั่ง|commands)\b",
    prefix="/help"
))
async def process_help(message, user_id=None, session_id=None, **kwargs):
    """Process a help request"""
    help_text = """
    Here are the available commands:
    - Fortune telling: Ask about your fortune or horoscope
    - Image generation: Ask me to generate an image
    - Help: Show this help message
    
    You can also use JSON format to specify commands explicitly.
    """
    
    return ToolResult(
        success=True,
        handled=True,
        response=help_text,
        data={"context": "help"}
    )

@tool_handler.register(ToolFunction(
    name="fortune_calculate",
    description="Calculate a fortune reading from a birthdate",
    pattern=r"\b(ดูดวง|fortune|horoscope|zodiac).+(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b"
))
async def process_fortune_with_date(message, user_id=None, session_id=None, **kwargs):
    """Process a fortune request with a birthdate included"""
    # Extract the birthdate using regex
    match = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", message)
    if not match:
        return ToolResult(
            success=False,
            handled=False,
            error="Could not parse birthdate"
        )
    
    year, month, day = match.groups()
    birthdate = f"{year}-{int(month):02d}-{int(day):02d}"
    
    try:
        # Validate date
        datetime.strptime(birthdate, "%Y-%m-%d")
        
        # Calculate fortune
        fortune_result = calculate_fortune(birthdate)
        
        # Enrich the calculation with interpretations
        enriched_fortune = enrich_fortune_calculation(fortune_result)
        
        # Extract key information for the response
        base1 = fortune_result.get("base1", {})
        base2 = fortune_result.get("base2", {})
        base3 = fortune_result.get("base3", {})
        
        # Create a simple text response
        base1_str = ", ".join([f"{k}: {v}" for k, v in base1.items()])
        base2_str = ", ".join([f"{k}: {v}" for k, v in base2.items()])
        base3_str = ", ".join([f"{k}: {v}" for k, v in base3.items()])
        
        response = f"Fortune calculation for birthdate {birthdate}:\n\n"
        response += f"Base 1 (Day): {base1_str}\n"
        response += f"Base 2 (Month): {base2_str}\n"
        response += f"Base 3 (Year): {base3_str}\n\n"
        
        # Add summary if available
        if "summary" in enriched_fortune:
            response += f"Summary: {enriched_fortune['summary']}\n\n"
        
        # Add most important interpretations
        if "combination_interpretations" in enriched_fortune and enriched_fortune["combination_interpretations"]:
            top_interpretations = enriched_fortune["combination_interpretations"][:3]
            response += "Key interpretations:\n"
            for interp in top_interpretations:
                response += f"- {interp.get('heading', '')}: {interp.get('meaning', '')[:100]}...\n"
        
        return ToolResult(
            success=True,
            handled=True,
            response=response,
            data={
                "context": "fortune_calculation",
                "birthdate": birthdate,
                "fortune_result": fortune_result,
                "enriched_fortune": enriched_fortune
            }
        )
    except ValueError as e:
        return ToolResult(
            success=False,
            handled=True,
            response=f"Invalid date format: {str(e)}. Please provide a valid date in YYYY-MM-DD format.",
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Error calculating fortune: {str(e)}", exc_info=True)
        return ToolResult(
            success=False,
            handled=True,
            response=f"Error calculating fortune: {str(e)}",
            error=str(e)
        )

@tool_handler.register(ToolFunction(
    name="json_fortune",
    description="Process a JSON fortune request",
    pattern=r"\{.*birthdate.*\}"
))
async def process_json_fortune(message, user_id=None, session_id=None, **kwargs):
    """Process a fortune request in JSON format"""
    try:
        # Try to parse the message as JSON
        if not isinstance(message, dict):
            data = json.loads(message)
        else:
            data = message
            
        # Check if this is a fortune request
        if "birthdate" in data:
            birthdate = data["birthdate"]
            
            # Calculate fortune
            fortune_result = calculate_fortune(birthdate)
            
            # Enrich the calculation with interpretations
            enriched_fortune = enrich_fortune_calculation(fortune_result)
            
            return ToolResult(
                success=True,
                handled=True,
                response=f"Fortune calculation for birthdate {birthdate} completed successfully.",
                data={
                    "context": "fortune_calculation",
                    "birthdate": birthdate,
                    "fortune_result": fortune_result,
                    "enriched_fortune": enriched_fortune
                }
            )
    except json.JSONDecodeError:
        # Not valid JSON, let it be handled by another tool
        return ToolResult(success=True, handled=False)
    except Exception as e:
        logger.error(f"Error processing JSON fortune request: {str(e)}", exc_info=True)
        return ToolResult(
            success=False,
            handled=True,
            response=f"Error processing fortune request: {str(e)}",
            error=str(e)
        )

@tool_handler.register(ToolFunction(
    name="test",
    description="Test tool to demonstrate functionality",
    pattern=r"\btest\b",
    prefix="/test"
))
async def process_test(message, user_id=None, session_id=None, **kwargs):
    """Process a test request"""
    return ToolResult(
        success=True,
        handled=True,
        response="This is a test response from the tool handler system. Your message was processed successfully.",
        data={
            "context": "test",
            "original_message": message,
            "timestamp": datetime.now().isoformat()
        }
    )

@tool_handler.register(ToolFunction(
    name="thai_wedding_date",
    description="Process requests about auspicious wedding dates in Thai",
    pattern=r"(ฤกษ์แต่งงาน|วันแต่งงาน|มงคลแต่งงาน|แต่งงาน).+(ปีนี้|ดี|มงคล)"
))
async def process_wedding_date_request(message, user_id=None, session_id=None, **kwargs):
    """Process a request for auspicious wedding dates in Thai"""
    return ToolResult(
        success=True,
        handled=True,
        response="สวัสดีค่ะ 😊 สำหรับฤกษ์แต่งงานที่ดีในปีนี้นั้น ขึ้นอยู่กับวันเดือนปีเกิดของทั้งคู่ค่ะ เพื่อให้ได้ฤกษ์ที่เป็นมงคลและเหมาะสมที่สุด รบกวนคุณช่วยบอกวันเดือนปีเกิดของคุณและคู่ของคุณในรูปแบบ YYYY-MM-DD ได้ไหมคะ? 🗓️✨ ขอบคุณค่ะ!",
        data={
            "context": "wedding_date_request",
            "status": "awaiting_birthdate"
        }
    )

@tool_handler.register(ToolFunction(
    name="thai_birthdate_format",
    description="Process birthdates in DD-MM-YYYY format",
    pattern=r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b"
))
async def process_thai_birthdate_format(message, user_id=None, session_id=None, **kwargs):
    """Process a message containing a birthdate in DD-MM-YYYY format"""
    # Extract the birthdate using regex
    match = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", message)
    if not match:
        return ToolResult(
            success=False,
            handled=False,
            error="Could not parse birthdate"
        )
    
    day, month, year = match.groups()
    
    # Convert to YYYY-MM-DD format
    birthdate = f"{year}-{int(month):02d}-{int(day):02d}"
    
    # Check if this is the first or second birthdate
    try:
        # Try to get session information to determine the context
        # This is just a placeholder - implement the actual logic for checking session state
        # Here we'd check if the session already has one birthdate recorded
        
        # For this example, we'll just respond with a request for the second birthdate
        return ToolResult(
            success=True,
            handled=True,
            response=f"ขอบคุณค่ะ 😊 นี่คือวันเกิดของคุณคือ {int(day)} {get_thai_month_name(int(month))} {year} แต่ยังขาดวันเดือนปีเกิดของคู่ของคุณค่ะ รบกวนบอกวันเกิดของคู่ของคุณในรูปแบบ YYYY-MM-DD ด้วยนะคะ เพื่อที่เราจะได้คำนวณฤกษ์แต่งงานที่ดีในปีนี้ค่ะ 🗓️✨",
            data={
                "context": "birthdate_provided",
                "birthdate": birthdate,
                "status": "awaiting_partner_birthdate"
            }
        )
    except Exception as e:
        logger.error(f"Error processing Thai birthdate format: {str(e)}", exc_info=True)
        return ToolResult(
            success=True,
            handled=True,
            response=f"ขอบคุณสำหรับวันเกิด {int(day)} {get_thai_month_name(int(month))} {year} ค่ะ กรุณาบอกวันเกิดในรูปแบบ YYYY-MM-DD หรือ DD-MM-YYYY ค่ะ",
            data={
                "context": "birthdate_provided",
                "birthdate": birthdate
            }
        )

@tool_handler.register(ToolFunction(
    name="multiple_birthdates",
    description="Process messages with multiple birthdates for wedding date calculation",
    pattern=r".*\d{1,2}[-/]\d{1,2}[-/]\d{4}.*\d{1,2}[-/]\d{1,2}[-/]\d{4}"
))
async def process_multiple_birthdates(message, user_id=None, session_id=None, **kwargs):
    """Process a message containing multiple birthdates for wedding calculation"""
    # Try to extract two birthdates
    matches = re.findall(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", message)
    if len(matches) < 2:
        # Try YYYY-MM-DD format
        matches = re.findall(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", message)
        if len(matches) < 2:
            return ToolResult(
                success=False,
                handled=False,
                error="Not enough birthdates found"
            )
    
    # Process the birthdates
    birthdates = []
    for match in matches[:2]:  # Take just the first two matches
        if len(match[0]) == 4:  # YYYY-MM-DD format
            year, month, day = match
            birthdates.append(f"{year}-{int(month):02d}-{int(day):02d}")
        else:  # DD-MM-YYYY format
            day, month, year = match
            birthdates.append(f"{year}-{int(month):02d}-{int(day):02d}")
    
    # Calculate wedding dates based on the birthdates
    # This would call your wedding date calculation function
    wedding_dates = calculate_wedding_dates(birthdates[0], birthdates[1])
    
    response = f"ขอบคุณสำหรับข้อมูลวันเกิดค่ะ 😊 ตอนนี้เราได้วันเกิดของทั้งคู่แล้ว\n\n"
    response += "ฤกษ์แต่งงานที่ดีสำหรับคุณทั้งคู่ในปีนี้มีดังนี้:\n"
    
    # Add some example wedding dates - replace with your actual calculation
    response += "1. วันเสาร์ที่ 15 มิถุนายน 2024 (เวลา 10:29 น.)\n"
    response += "2. วันอาทิตย์ที่ 7 กรกฎาคม 2024 (เวลา 09:19 น.)\n"
    response += "3. วันเสาร์ที่ 14 กันยายน 2024 (เวลา 10:59 น.)\n"
    response += "4. วันอาทิตย์ที่ 10 พฤศจิกายน 2024 (เวลา 10:09 น.)\n\n"
    
    response += "วันเวลาเหล่านี้เป็นช่วงที่ดวงดาวโคจรมาอยู่ในตำแหน่งที่เป็นมงคล ส่งเสริมความรักความเข้าใจและความมั่งคั่งให้กับชีวิตคู่ค่ะ 💑✨"
    
    return ToolResult(
        success=True,
        handled=True,
        response=response,
        data={
            "context": "wedding_dates_calculation",
            "person1_birthdate": birthdates[0],
            "person2_birthdate": birthdates[1],
            "wedding_dates": wedding_dates if 'wedding_dates' in locals() else []
        }
    )

# Helper function for Thai month names
def get_thai_month_name(month_number):
    thai_months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    
    if 1 <= month_number <= 12:
        return thai_months[month_number - 1]
    return str(month_number)

# Placeholder for the wedding date calculation function
def calculate_wedding_dates(birthdate1, birthdate2):
    # This would implement your actual wedding date calculation logic
    # For now, return some example dates
    current_year = datetime.now().year
    return [
        f"{current_year}-06-15 10:29:00",
        f"{current_year}-07-07 09:19:00",
        f"{current_year}-09-14 10:59:00",
        f"{current_year}-11-10 10:09:00"
    ]

@tool_handler.register(ToolFunction(
    name="wedding_date_calculation",
    description="Calculate auspicious wedding dates when two birthdates are known",
    pattern=r"(คำนวณฤกษ์แต่งงาน|หาฤกษ์แต่งงาน|ฤกษ์แต่งงานที่ดี)"
))
async def process_wedding_date_calculation(message, user_id=None, session_id=None, **kwargs):
    """Calculate wedding dates when birthdates have been provided"""
    # In a real implementation, you would retrieve the stored birthdates for this user/session
    # and then calculate the wedding dates
    
    # For this example, we'll just send a response asking for birthdates
    return ToolResult(
        success=True,
        handled=True,
        response="เพื่อคำนวณฤกษ์แต่งงานที่ดี กรุณาแจ้งวันเกิดของคุณและคู่ของคุณในรูปแบบ YYYY-MM-DD หรือ DD-MM-YYYY ค่ะ",
        data={
            "context": "wedding_date_calculation",
            "status": "awaiting_birthdates"
        }
    )

@tool_handler.register(ToolFunction(
    name="fortune_followup",
    description="Process follow-up questions about a previous fortune reading",
    pattern=r"(อธิบายเพิ่มเติม|บอกอีก|อะไรคือ|ความหมาย|รายละเอียด|ขยายความ|เรื่อง).*(ดวง|โชคชะตา|อิทธิพล|ฐาน|เลข|กดุมภะ|อัตตะ|หินะ|ธานัง|ปิตา|มาตา|โภคา|มัชฌิมา|ตะนุ|สหัชชะ|พันธุ|ปุตตะ|อริ|ปัตนิ|มรณะ|สุภะ|กัมมะ|ลาภะ|พยายะ|ทาสา|ทาสี)"
))
async def process_fortune_followup(message, user_id=None, session_id=None, **kwargs):
    """Process follow-up questions about a previous fortune reading by analyzing the content
    of the fortune result that should be stored in the chat session context."""
    
    # This would need a way to retrieve previous fortune data from the session
    # For now, we'll simulate that this data is available
    
    try:
        # In a real implementation, you would:
        # 1. Check if there's stored fortune data for this session
        # 2. Determine what aspect of the fortune the user is asking about
        # 3. Extract and provide the relevant information
        
        # Detect which aspect of the fortune reading they're asking about
        aspects = {
            "ฐาน1": ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"],
            "ฐาน2": ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"],
            "ฐาน3": ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]
        }
        
        # Check which specific aspect they're asking about
        aspect_match = None
        category_match = None
        
        for base_name, categories in aspects.items():
            for category in categories:
                if category in message:
                    aspect_match = base_name
                    category_match = category
                    break
            if aspect_match:
                break
        
        # If we found a specific category they're asking about
        if category_match:
            # Get the meaning for this category
            from app.utils.fortune_calculator import get_category_meaning, determine_influence
            
            meaning = get_category_meaning(category_match)
            influence = determine_influence(category_match)
            
            response = f"'{category_match}' คือหนึ่งในองค์ประกอบของการดูดวงในระบบเลข 7 ฐาน 9 ค่ะ\n\n"
            response += f"ความหมาย: {meaning}\n"
            response += f"ลักษณะอิทธิพล: {influence}\n\n"
            
            response += "ตัวเลขที่สูง (5-7) แสดงถึงอิทธิพลที่มีผลมากในชีวิตคุณ ส่วนตัวเลขที่ต่ำ (1-3) แสดงถึงอิทธิพลที่มีผลน้อย\n\n"
            
            response += "หากต้องการคำอธิบายเพิ่มเติมเกี่ยวกับดวงชะตาของคุณโดยเฉพาะ กรุณาถามคำถามที่เฉพาะเจาะจงค่ะ เช่น 'บอกเพิ่มเติมเกี่ยวกับอิทธิพลของมาตาและกดุมภะ'"
            
            return ToolResult(
                success=True,
                handled=True,
                response=response,
                data={
                    "context": "fortune_followup",
                    "category": category_match,
                    "aspect": aspect_match,
                    "meaning": meaning,
                    "influence": influence
                }
            )
        elif "ฐาน" in message or "เลข 7 ฐาน 9" in message:
            # They're asking about the bases or system in general
            response = "เลข 7 ฐาน 9 คือระบบการทำนายโชคชะตาแบบไทย โดยแบ่งการวิเคราะห์เป็น 3 ฐานหลัก:\n\n"
            response += "ฐาน 1 (วันเกิด): อัตตะ, หินะ, ธานัง, ปิตา, มาตา, โภคา, มัชฌิมา\n"
            response += "ฐาน 2 (เดือนเกิด): ตะนุ, กดุมภะ, สหัชชะ, พันธุ, ปุตตะ, อริ, ปัตนิ\n"
            response += "ฐาน 3 (ปีเกิด): มรณะ, สุภะ, กัมมะ, ลาภะ, พยายะ, ทาสา, ทาสี\n\n"
            
            response += "แต่ละด้านมีหมายเลขจาก 1-7 กำกับ ตัวเลขที่สูงแสดงถึงอิทธิพลที่มากในชีวิต ตัวเลขที่ต่ำแสดงถึงอิทธิพลที่น้อย\n\n"
            
            response += "คุณอยากทราบรายละเอียดเกี่ยวกับด้านใดเป็นพิเศษหรือไม่คะ?"
            
            return ToolResult(
                success=True,
                handled=True,
                response=response,
                data={
                    "context": "fortune_explanation",
                    "topic": "general_bases"
                }
            )
        else:
            # General follow-up about fortune
            response = "ในการดูดวงด้วยระบบเลข 7 ฐาน 9 นั้น เราวิเคราะห์จากวันเดือนปีเกิดของคุณเพื่อคำนวณค่าอิทธิพลในด้านต่างๆ ของชีวิต\n\n"
            
            response += "แต่ละด้านจะมีค่าอิทธิพลตั้งแต่ 1-7 โดย:\n"
            response += "- ค่า 1-2: อิทธิพลน้อยมาก\n"
            response += "- ค่า 3-4: อิทธิพลปานกลาง\n"
            response += "- ค่า 5-7: อิทธิพลสูง\n\n"
            
            response += "นอกจากนี้ยังมีการวิเคราะห์ความสัมพันธ์ระหว่างด้านต่างๆ เพื่อให้ภาพที่สมบูรณ์มากขึ้น\n\n"
            
            response += "คุณอยากทราบรายละเอียดเกี่ยวกับด้านใดเป็นพิเศษไหมคะ?"
            
            return ToolResult(
                success=True,
                handled=True,
                response=response,
                data={
                    "context": "fortune_explanation",
                    "topic": "general"
                }
            )
    except Exception as e:
        logger.error(f"Error processing fortune follow-up: {str(e)}", exc_info=True)
        
        # Fallback response
        response = "ขออภัยค่ะ ฉันไม่สามารถประมวลผลคำถามเกี่ยวกับดวงชะตาของคุณได้ในขณะนี้\n\n"
        response += "คุณอาจต้องทำการดูดวงใหม่ด้วยการให้วันเดือนปีเกิดของคุณก่อน หรือลองถามคำถามในรูปแบบอื่นค่ะ"
        
        return ToolResult(
            success=False,
            handled=True,
            response=response,
            error=str(e)
        )

@tool_handler.register(ToolFunction(
    name="fortune_combination_followup",
    description="Process follow-up questions about specific combinations in a fortune reading",
    pattern=r"(อธิบาย|ความหมาย|ความสัมพันธ์|เรื่อง|ระหว่าง).*(และ|กับ|&).*(อัตตะ|หินะ|ธานัง|ปิตา|มาตา|โภคา|มัชฌิมา|ตะนุ|กดุมภะ|สหัชชะ|พันธุ|ปุตตะ|อริ|ปัตนิ|มรณะ|สุภะ|กัมมะ|ลาภะ|พยายะ|ทาสา|ทาสี)"
))
async def process_fortune_combination_followup(message, user_id=None, session_id=None, **kwargs):
    """Process follow-up questions about specific combinations of categories in a fortune reading"""
    
    try:
        # Get all possible categories from all bases
        all_categories = [
            "อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา",  # Base 1
            "ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ",  # Base 2
            "มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"    # Base 3
        ]
        
        # Find which categories are mentioned in the message
        mentioned_categories = []
        for category in all_categories:
            if category in message:
                mentioned_categories.append(category)
        
        # If we found at least two categories
        if len(mentioned_categories) >= 2:
            # For simplicity, we'll use the first two mentioned categories
            cat1, cat2 = mentioned_categories[0], mentioned_categories[1]
            
            # Import necessary functions from fortune calculator
            from app.utils.fortune_calculator import (
                get_category_meaning, 
                determine_influence, 
                determine_combined_influence,
                generate_heading_for_combination,
                generate_meaning_for_combination
            )
            
            # Get meanings and influences for each category
            cat1_meaning = get_category_meaning(cat1)
            cat2_meaning = get_category_meaning(cat2)
            cat1_influence = determine_influence(cat1)
            cat2_influence = determine_influence(cat2)
            combined_influence = determine_combined_influence(cat1, cat2)
            
            # In a real implementation, we would look up the actual values from the stored fortune calculation
            # For now, we'll use placeholder values
            cat1_value = 5  # Placeholder - would come from user's actual fortune data
            cat2_value = 4  # Placeholder - would come from user's actual fortune data
            
            # Generate a heading and meaning for this combination
            heading = generate_heading_for_combination(cat1, cat2, cat1_value, cat2_value)
            meaning = generate_meaning_for_combination(cat1, cat2, cat1_meaning, cat2_meaning, cat1_value, cat2_value)
            
            # Create a response
            response = f"เกี่ยวกับความสัมพันธ์ระหว่าง '{cat1}' และ '{cat2}':\n\n"
            response += f"**{heading}**\n\n"
            response += f"{meaning}\n\n"
            response += f"อิทธิพลโดยรวม: {combined_influence}\n\n"
            
            # Add additional explanation about what this means
            response += "ความสัมพันธ์นี้แสดงถึงการเชื่อมโยงระหว่างด้านต่างๆ ในชีวิตของคุณ "
            
            if combined_influence == "ดี":
                response += "ซึ่งมีแนวโน้มที่จะส่งเสริมกันในทางที่ดี เป็นจุดแข็งที่ควรใช้ประโยชน์"
            elif combined_influence == "กลาง":
                response += "ซึ่งมีทั้งด้านที่ส่งเสริมและท้าทายกัน ควรสร้างความสมดุลให้กับทั้งสองด้านนี้"
            else:
                response += "ซึ่งอาจมีความท้าทายหรือความขัดแย้งที่ควรระมัดระวัง"
            
            return ToolResult(
                success=True,
                handled=True,
                response=response,
                data={
                    "context": "fortune_combination_followup",
                    "combination": f"{cat1}-{cat2}",
                    "heading": heading,
                    "meaning": meaning,
                    "influence": combined_influence
                }
            )
        else:
            # Ask for more specific information
            response = "หากต้องการทราบความสัมพันธ์ระหว่างด้านต่างๆ ในดวงชะตา กรุณาระบุด้านที่ต้องการทราบให้ชัดเจน\n\n"
            response += "ตัวอย่างเช่น 'อธิบายความสัมพันธ์ระหว่างมาตาและกดุมภะ' หรือ 'ความหมายของอัตตะและธานัง'\n\n"
            
            response += "ด้านต่างๆ ในดวงชะตาประกอบด้วย:\n"
            response += "- ฐาน 1 (วันเกิด): อัตตะ, หินะ, ธานัง, ปิตา, มาตา, โภคา, มัชฌิมา\n"
            response += "- ฐาน 2 (เดือนเกิด): ตะนุ, กดุมภะ, สหัชชะ, พันธุ, ปุตตะ, อริ, ปัตนิ\n"
            response += "- ฐาน 3 (ปีเกิด): มรณะ, สุภะ, กัมมะ, ลาภะ, พยายะ, ทาสา, ทาสี"
            
            return ToolResult(
                success=True,
                handled=True,
                response=response,
                data={
                    "context": "fortune_combination_request",
                    "status": "awaiting_specific_combination"
                }
            )
    except Exception as e:
        logger.error(f"Error processing fortune combination follow-up: {str(e)}", exc_info=True)
        
        # Fallback response
        response = "ขออภัยค่ะ ฉันไม่สามารถอธิบายความสัมพันธ์ในดวงชะตาที่คุณสอบถามได้ในขณะนี้\n\n"
        response += "คุณอาจต้องทำการดูดวงใหม่ด้วยการให้วันเดือนปีเกิดของคุณก่อน หรือลองถามคำถามในรูปแบบอื่นค่ะ"
        
        return ToolResult(
            success=False,
            handled=True,
            response=response,
            error=str(e)
        ) 