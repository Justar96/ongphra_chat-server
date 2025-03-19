# app/utils/fortune_tool.py
import re
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

from app.core.logging import get_logger
from app.services.session_service import get_session_manager
from app.services.reading_service import get_reading_service
from app.domain.meaning import FortuneReading

logger = get_logger(__name__)

# Define fortune-related keywords to identify fortune requests
FORTUNE_KEYWORDS = [
    'ดวง', 'ดูดวง', 'ทำนาย', 'โหราศาสตร์', 'ชะตา', 'ไพ่ยิปซี', 'ราศี', 'ทำนายดวงชะตา',
    'fortune', 'horoscope', 'predict', 'future', 'astrology', 'tarot', 'destiny',
    'ดูดวงชะตา', 'ทำนาย', 'ดวงชะตา', 'ดูดวงด้วย', 'ทำนายด้วย', 'ฟันธง'
]

# Date pattern for different formats
DATE_PATTERNS = [
    r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
    r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-YYYY
    r'(\d{1,2})\s+(?:มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+(\d{4})'  # DD Month YYYY in Thai
]

# Month name to number mapping for Thai dates
THAI_MONTHS = {
    'มกราคม': 1,
    'กุมภาพันธ์': 2,
    'มีนาคม': 3,
    'เมษายน': 4,
    'พฤษภาคม': 5,
    'มิถุนายน': 6,
    'กรกฎาคม': 7,
    'สิงหาคม': 8,
    'กันยายน': 9,
    'ตุลาคม': 10,
    'พฤศจิกายน': 11,
    'ธันวาคม': 12
}

async def handle_fortune_request(user_message: str, user_id: str = None) -> Dict[str, Any]:
    """
    Tool function for AI to handle fortune reading requests.
    
    This function:
    1. Checks if the message is asking for a fortune reading
    2. Extracts birth date from the message if present
    3. Checks if birth date is already stored in the session
    4. Returns appropriate response based on available information
    
    Args:
        user_message: The user's message/query
        user_id: User identifier for session tracking
        
    Returns:
        A dictionary with the following fields:
        - needs_birthdate: Boolean indicating if we need to ask for birth date
        - is_fortune_request: Boolean indicating if this is a fortune request
        - fortune_reading: Fortune reading result if available
        - user_message: Original user message
        - extracted_birthdate: Birth date extracted from message (if any)
    """
    logger.info(f"Processing potential fortune request: {user_message[:50]}...")
    
    # Initialize result dictionary
    result = {
        "needs_birthdate": False,
        "is_fortune_request": False,
        "fortune_reading": None,
        "user_message": user_message,
        "extracted_birthdate": None
    }
    
    # 1. Check if this is a fortune request
    is_fortune_request = any(keyword in user_message.lower() for keyword in FORTUNE_KEYWORDS)
    result["is_fortune_request"] = is_fortune_request
    
    if not is_fortune_request:
        logger.debug("Not a fortune request, returning early")
        return result
        
    # Get the session manager
    session_manager = get_session_manager()
    
    # Generate a user ID if not provided
    if not user_id:
        import uuid
        user_id = str(uuid.uuid4())
        logger.info(f"Generated new user_id: {user_id}")
    
    # 2. Extract birth date from message if present
    extracted_date, extracted_date_text = extract_birth_date(user_message)
    
    if extracted_date:
        logger.info(f"Extracted birth date: {extracted_date.strftime('%Y-%m-%d')} from: {extracted_date_text}")
        thai_day = None  # Will be calculated by the service
        session_manager.save_birth_info(user_id, extracted_date, thai_day)
        result["extracted_birthdate"] = extracted_date.strftime("%Y-%m-%d")
    
    # 3. Check for existing birth info in session
    has_birth_info = False
    birth_date_obj = None
    thai_day = None
    
    birth_info = session_manager.get_birth_info(user_id)
    if birth_info:
        try:
            birth_date_obj = datetime.strptime(birth_info["birth_date"], "%Y-%m-%d")
            thai_day = birth_info["thai_day"]
            has_birth_info = True
            logger.info(f"Using stored birth info: {birth_date_obj.strftime('%Y-%m-%d')}, {thai_day}")
        except (ValueError, KeyError):
            logger.warning("Invalid stored birth info")
    
    # 4. Determine next steps
    if has_birth_info or extracted_date:
        # We have birth info, process fortune reading
        if not birth_date_obj and extracted_date:
            birth_date_obj = extracted_date
        
        try:
            # Get reading service
            reading_service = await get_reading_service()
            
            # Get fortune reading
            reading = await reading_service.get_fortune_reading(
                birth_date=birth_date_obj,
                thai_day=thai_day,
                question=user_message,
                user_id=user_id
            )
            
            result["fortune_reading"] = reading.dict()
        except Exception as e:
            logger.error(f"Error getting fortune reading: {str(e)}", exc_info=True)
            result["fortune_reading"] = {
                "birth_date": birth_date_obj.strftime("%Y-%m-%d") if birth_date_obj else "",
                "thai_day": thai_day if thai_day else "",
                "question": user_message,
                "heading": "เกิดข้อผิดพลาด",
                "meaning": f"เกิดข้อผิดพลาดในการวิเคราะห์: {str(e)}",
                "influence_type": "ไม่ทราบ"
            }
    else:
        # We need to ask for birth date
        result["needs_birthdate"] = True
        logger.info("No birth date available, need to ask for it")
    
    return result

def extract_birth_date(text: str) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Extract birth date from text using various patterns
    
    Args:
        text: The text to extract date from
        
    Returns:
        Tuple of (datetime object if found, extracted text)
    """
    # Try standard date formats: DD/MM/YYYY, YYYY/MM/DD
    for pattern in DATE_PATTERNS:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                matched_text = match.group(0)
                
                # First pattern: DD/MM/YYYY
                if pattern == DATE_PATTERNS[0]:
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        return datetime(year, month, day), matched_text
                
                # Second pattern: YYYY/MM/DD
                elif pattern == DATE_PATTERNS[1]:
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        return datetime(year, month, day), matched_text
                
                # Third pattern: Thai format (DD Month YYYY)
                elif pattern == DATE_PATTERNS[2]:
                    day = int(match.group(1))
                    thai_month = match.group(2)
                    year = int(match.group(3))
                    
                    # Convert Thai month name to number
                    if thai_month in THAI_MONTHS:
                        month = THAI_MONTHS[thai_month]
                        if 1 <= day <= 31 and 1900 <= year <= 2100:
                            return datetime(year, month, day), matched_text
            
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse date from {match.group(0)}: {str(e)}")
                continue
    
    return None, None 