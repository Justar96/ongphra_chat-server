import logging
from datetime import datetime  # Import datetime class directly
from typing import Dict, List, Tuple, Any, Optional
from itertools import combinations
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from .db_utils import get_db_session, get_fortune_pair_interpretation, get_category_pair_heading, get_category_thai_name
    db_utils_available = True
except ImportError:
    logger.warning("Database utilities not available. Will use generic meanings.")
    db_utils_available = False

# Define the schema for the fortune tool
FORTUNE_TOOL_SCHEMA = {
    "name": "calculate_fortune",
    "description": "Calculate Thai fortune based on birthdate",
    "parameters": {
        "type": "object",
        "properties": {
            "birthdate": {
                "type": "string",
                "description": "Birthdate in YYYY-MM-DD format"
            },
            "detail_level": {
                "type": "string",
                "enum": ["simple", "normal", "detailed"],
                "description": "Level of detail for the fortune calculation"
            }
        },
        "required": ["birthdate"]
    }
}

def query_pair_meaning_from_db(category_a: str, category_b: str, value_a: int, value_b: int) -> Dict[str, Any]:
    """
    Query the meaning of a pair of categories from the database.
    
    Args:
        category_a: The name of the first category
        category_b: The name of the second category
        value_a: The value of the first category (1-7)
        value_b: The value of the second category (1-7)
        
    Returns:
        A dictionary with the meaning details including heading, meaning, and influence
    """
    try:
        if not db_utils_available:
            return generate_generic_pair_meaning(category_a, category_b, value_a, value_b, as_dict=True)
            
        # Query the database for the interpretation
        interpretation = get_fortune_pair_interpretation(category_a, category_b, value_a, value_b)
        
        if interpretation:
            return interpretation
        
        # If no interpretation found, generate a generic one
        heading = get_category_pair_heading(category_a, category_b)
        
        meaning = generate_generic_pair_meaning(category_a, category_b, value_a, value_b)
        
        return {
            "heading": heading,
            "meaning": meaning,
            "influence": "ผสมผสาน"  # Default influence
        }
    except Exception as e:
        logger.error(f"Error querying pair meaning: {e}")
        return generate_generic_pair_meaning(category_a, category_b, value_a, value_b, as_dict=True)

def get_thai_name(category: str) -> str:
    """
    Get the Thai name for a category.
    If db_utils is not available, use a fallback mapping.
    
    Args:
        category: The English name of the category
        
    Returns:
        The Thai name of the category
    """
    if db_utils_available:
        thai_name = get_category_thai_name(category)
        if thai_name:
            return thai_name
    
    # Fallback mapping
    thai_names = {
        # Base 1
        "attana": "อัตตะ",
        "hina": "หินะ",
        "thana": "ธานัง",
        "pita": "ปิตา",
        "mata": "มาตา",
        "bhoga": "โภคา",
        "majjhima": "มัชฌิมา",
        
        # Base 2
        "tanu": "ตะนุ",
        "kadumpha": "กดุมภะ",
        "sahajja": "สหัชชะ",
        "phantu": "พันธุ",
        "putta": "ปุตตะ",
        "ari": "อริ",
        "patni": "ปัตนิ",
        
        # Base 3
        "marana": "มรณะ",
        "subha": "สุภะ",
        "kamma": "กัมมะ",
        "labha": "ลาภะ",
        "phayaya": "พยายะ",
        "thasa": "ทาสา",
        "thasi": "ทาสี"
    }
    
    return thai_names.get(category, category)

def get_default_heading(category_a: str, category_b: str) -> str:
    """
    Get a default heading for a pair of categories.
    
    Args:
        category_a: The English name of the first category
        category_b: The English name of the second category
        
    Returns:
        A default heading for the pair
    """
    a_thai = get_thai_name(category_a)
    b_thai = get_thai_name(category_b)
    
    # Specific headings for certain category combinations
    special_pairs = {
        frozenset(['thana', 'kadumpha']): "การเงินและรายได้",
        frozenset(['kamma', 'labha']): "การงานและโชคลาภ",
        frozenset(['attana', 'tanu']): "ตัวตนและบุคลิกภาพ",
        frozenset(['patni', 'putta']): "ครอบครัวและความสัมพันธ์"
    }
    
    pair_key = frozenset([category_a, category_b])
    if pair_key in special_pairs:
        return special_pairs[pair_key]
    
    # Default heading
    return f"ความสัมพันธ์ระหว่าง{a_thai}และ{b_thai}"

def generate_generic_pair_meaning(category_a: str, category_b: str, value_a: int, value_b: int, as_dict: bool = False) -> Dict[str, Any] or str:
    """
    Generate a generic meaning for a pair of categories based on their values.
    
    Args:
        category_a: The name of the first category
        category_b: The name of the second category
        value_a: The value of the first category (1-7)
        value_b: The value of the second category (1-7)
        as_dict: Whether to return the meaning as a dictionary
        
    Returns:
        A string with the meaning or a dictionary with heading, meaning, and influence
    """
    # Get Thai names
    a_thai = get_thai_name(category_a)
    b_thai = get_thai_name(category_b)
    
    # Define meaning based on values
    if value_a >= 5 and value_b >= 5:
        # Both high values
        meaning = f"คุณมีความโดดเด่นในเรื่อง{a_thai}และ{b_thai} ซึ่งส่งผลดีต่อชีวิตของคุณ ความสามารถนี้จะช่วยให้คุณประสบความสำเร็จในหลายด้าน"
        influence = "ดี"
    elif value_a <= 3 and value_b <= 3:
        # Both low values
        meaning = f"คุณอาจพบความท้าทายในเรื่อง{a_thai}และ{b_thai} ซึ่งอาจส่งผลต่อการตัดสินใจและการดำเนินชีวิต ควรระมัดระวังและพัฒนาในด้านนี้"
        influence = "ต้องระวัง"
    elif abs(value_a - value_b) >= 3:
        # Large difference between values
        higher = a_thai if value_a > value_b else b_thai
        lower = b_thai if value_a > value_b else a_thai
        meaning = f"คุณมีความแข็งแกร่งใน{higher} แต่อาจต้องพัฒนาในเรื่อง{lower} ความไม่สมดุลนี้อาจส่งผลต่อการตัดสินใจและแนวทางชีวิตของคุณ"
        influence = "ผสมผสาน"
    else:
        # Balanced values
        meaning = f"คุณมีความสมดุลระหว่าง{a_thai}และ{b_thai} ซึ่งช่วยให้คุณจัดการชีวิตได้อย่างราบรื่น การรักษาสมดุลนี้จะช่วยให้คุณประสบความสำเร็จในระยะยาว"
        influence = "ดี"
    
    if as_dict:
        heading = get_default_heading(category_a, category_b)
        return {
            "heading": heading,
            "meaning": meaning,
            "influence": influence
        }
    
    return meaning

def calculate_fortune(birthdate, detail_level="normal"):
    """
    Calculate fortune based on birthdate.
    
    Args:
        birthdate: Birthdate as a datetime object or string (YYYY-MM-DD format)
        detail_level: Level of detail (simple, normal, detailed)
        
    Returns:
        Dictionary with fortune calculation results
    """
    try:
        # Handle different date formats
        if isinstance(birthdate, str):
            try:
                if "-" in birthdate:
                    birthdate = datetime.strptime(birthdate, "%Y-%m-%d")
                elif "/" in birthdate:
                    if len(birthdate.split("/")[0]) == 4:
                        # YYYY/MM/DD
                        birthdate = datetime.strptime(birthdate, "%Y/%m/%d")
                    else:
                        # DD/MM/YYYY
                        birthdate = datetime.strptime(birthdate, "%d/%m/%Y")
                else:
                    raise ValueError(f"Unsupported date format: {birthdate}")
            except ValueError as e:
                logger.error(f"Error parsing date: {e}")
                raise ValueError(f"Invalid date format: {birthdate}. Please use YYYY-MM-DD format.")
        
        # Basic validation
        if not isinstance(birthdate, datetime):
            raise ValueError("Birthdate must be a datetime object or a string in YYYY-MM-DD format")
        
        # Extract date components
        birth_day = birthdate.day
        birth_month = birthdate.month
        birth_year = birthdate.year
        
        # Format the birthdate
        formatted_birthdate = birthdate.strftime("%d %B %Y")
        
        # Determine day of the week
        days_of_week = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
        day_of_week = days_of_week[birthdate.weekday()]
        
        # Calculate zodiac year
        zodiac_animals = ["ลิง", "ไก่", "สุนัข", "หมู", "หนู", "วัว", "เสือ", "กระต่าย", "มังกร", "งู", "ม้า", "แพะ"]
        zodiac_year = zodiac_animals[(birth_year - 4) % 12]
        
        # Calculate base numbers
        day = birth_day
        month = birth_month
        year = birth_year
        
        # Base 1
        base1 = (day + month + (year % 100)) % 7
        if base1 == 0:
            base1 = 7
            
        # Base 2
        base2 = (day + month + (year // 100)) % 7
        if base2 == 0:
            base2 = 7
            
        # Base 3
        base3 = (day + month + year) % 7
        if base3 == 0:
            base3 = 7
        
        # Define categories for each base
        base1_categories = [
            {"name": "attana", "thai_name": "อัตตะ", "meaning": "ตัวท่านเอง", "house_type": "กาลปักษ์"},
            {"name": "hina", "thai_name": "หินะ", "meaning": "ความผิดหวัง", "house_type": "กาลปักษ์"},
            {"name": "thana", "thai_name": "ธานัง", "meaning": "เรื่องเงิน ๆ ทอง ๆ", "house_type": "จร"},
            {"name": "pita", "thai_name": "ปิตา", "meaning": "พ่อหรือผู้ใหญ่ เรื่องนอกบ้าน", "house_type": "เกณฑ์ชะตา"},
            {"name": "mata", "thai_name": "มาตา", "meaning": "แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว", "house_type": "เกณฑ์ชะตา"},
            {"name": "bhoga", "thai_name": "โภคา", "meaning": "สินทรัพย์", "house_type": "จร"},
            {"name": "majjhima", "thai_name": "มัชฌิมา", "meaning": "เรื่องกลาง ๆ ไม่หนักหนา", "house_type": "กาลปักษ์"},
        ]
        
        base2_categories = [
            {"name": "tanu", "thai_name": "ตะนุ", "meaning": "ตัวท่านเอง", "house_type": "จร"},
            {"name": "kadumpha", "thai_name": "กดุมภะ", "meaning": "รายได้รายจ่าย", "house_type": "กาลปักษ์"},
            {"name": "sahajja", "thai_name": "สหัชชะ", "meaning": "เพื่อนฝูง การติดต่อ", "house_type": "กาลปักษ์"},
            {"name": "phantu", "thai_name": "พันธุ", "meaning": "ญาติพี่น้อง", "house_type": "เกณฑ์ชะตา"},
            {"name": "putta", "thai_name": "ปุตตะ", "meaning": "เรื่องลูก การเริ่มต้น", "house_type": "จร"},
            {"name": "ari", "thai_name": "อริ", "meaning": "ปัญหา อุปสรรค", "house_type": "กาลปักษ์"},
            {"name": "patni", "thai_name": "ปัตนิ", "meaning": "คู่ครอง", "house_type": "กาลปักษ์"},
        ]
        
        base3_categories = [
            {"name": "marana", "thai_name": "มรณะ", "meaning": "เรื่องเจ็บป่วย", "house_type": "กาลปักษ์"},
            {"name": "subha", "thai_name": "สุภะ", "meaning": "ความเจริญรุ่งเรือง", "house_type": "เกณฑ์ชะตา"},
            {"name": "kamma", "thai_name": "กัมมะ", "meaning": "หน้าที่การงาน", "house_type": "เกณฑ์ชะตา"},
            {"name": "labha", "thai_name": "ลาภะ", "meaning": "ลาภยศ โชคลาภ", "house_type": "จร"},
            {"name": "phayaya", "thai_name": "พยายะ", "meaning": "สิ่งไม่ดี เรื่องปิดบัง ซ่อนเร้น", "house_type": "กาลปักษ์"},
            {"name": "thasa", "thai_name": "ทาสา", "meaning": "เหน็จเหนื่อยเพื่อคนอื่น ส่วนรวม", "house_type": "กาลปักษ์"},
            {"name": "thasi", "thai_name": "ทาสี", "meaning": "การเหน็จเหนื่อยเพื่อตัวเอง", "house_type": "เกณฑ์ชะตา"},
        ]
        
        # Get top categories
        top_base1_category = base1_categories[base1-1]
        top_base2_category = base2_categories[base2-1]
        top_base3_category = base3_categories[base3-1]
        
        # Generate pairs
        pairs = []
        
        # Add top pairs (combinations of top categories)
        pairs.append({
            "category_a": top_base1_category["name"],
            "category_b": top_base2_category["name"],
            "thai_a": top_base1_category["thai_name"],
            "thai_b": top_base2_category["thai_name"],
            "value_a": 7,
            "value_b": 7
        })
        
        pairs.append({
            "category_a": top_base1_category["name"],
            "category_b": top_base3_category["name"],
            "thai_a": top_base1_category["thai_name"],
            "thai_b": top_base3_category["thai_name"],
            "value_a": 7,
            "value_b": 6
        })
        
        pairs.append({
            "category_a": top_base2_category["name"],
            "category_b": top_base3_category["name"],
            "thai_a": top_base2_category["thai_name"],
            "thai_b": top_base3_category["thai_name"],
            "value_a": 7,
            "value_b": 6
        })
        
        # Query meanings for each pair from the database
        top_pairs = []
        
        with get_db_session() as session:
            for i, pair in enumerate(pairs):
                category_a = pair["category_a"]
                category_b = pair["category_b"]
                value_a = pair["value_a"]
                value_b = pair["value_b"]
                thai_a = pair["thai_a"]
                thai_b = pair["thai_b"]
                
                # Get the interpretation from the database
                interp = get_fortune_pair_interpretation(category_a, category_b, value_a, value_b, session)
                
                if not interp:
                    # Generate a generic interpretation if none is found in the database
                    thai_a = get_category_thai_name(category_a, session) or pair["thai_a"]
                    thai_b = get_category_thai_name(category_b, session) or pair["thai_b"]
                    
                    heading = get_category_pair_heading(category_a, category_b, session) or f"ความสัมพันธ์ระหว่าง{thai_a}และ{thai_b}"
                    meaning = generate_generic_pair_meaning(category_a, category_b, value_a, value_b)
                    influence = "ผสมผสาน"
                else:
                    heading = interp["heading"]
                    meaning = interp["meaning"]
                    influence = interp.get("influence", "ผสมผสาน")
                
                pair_result = {
                    "rank": i + 1,
                    "heading": heading,
                    "categories": f"{thai_a} ({value_a}) + {thai_b} ({value_b})",
                    "meaning": meaning,
                    "influence": influence,
                    # Add these fields to match the test script expectations
                    "category_a": category_a,
                    "category_b": category_b,
                    "thai_name_a": thai_a,
                    "thai_name_b": thai_b,
                    "value_a": value_a,
                    "value_b": value_b
                }
                
                top_pairs.append(pair_result)
        
        # Generate a summary
        summary = f"""จากวันเกิด {formatted_birthdate} ({day_of_week}) {zodiac_year} พบว่า:

            คุณมีฐานที่ 1 ({base1}) โดดเด่นในด้าน{top_base1_category['thai_name']} ({top_base1_category['meaning']})
            คุณมีฐานที่ 2 ({base2}) โดดเด่นในด้าน{top_base2_category['thai_name']} ({top_base2_category['meaning']})
            คุณมีฐานที่ 3 ({base3}) โดดเด่นในด้าน{top_base3_category['thai_name']} ({top_base3_category['meaning']})

            ความโดดเด่นเหล่านี้แสดงถึงลักษณะเฉพาะของคุณ รวมถึงจุดแข็งและจุดที่ควรพัฒนา"""
            
        # Filter content based on detail level
        if detail_level == "simple":
            # For simple, just show summary and top categories
            top_pairs = top_pairs[:1]  # Only the most important pair
        elif detail_level == "normal":
            # For normal, include a few pairs
            top_pairs = top_pairs[:3]
        # For detailed, include all information (default)
            
        # Prepare the result
        result = {
            "birthdate": formatted_birthdate,
            "formatted_birthdate": formatted_birthdate,
            "day_of_week": day_of_week,
            "zodiac_year": zodiac_year,
            "bases": {
                "base1": base1,
                "base2": base2,
                "base3": base3
            },
            "top_categories": {
                "base1": {
                    "name": top_base1_category["name"],
                    "thai_name": top_base1_category["thai_name"],
                    "meaning": top_base1_category["meaning"],
                    "value": 7
                },
                "base2": {
                    "name": top_base2_category["name"],
                    "thai_name": top_base2_category["thai_name"],
                    "meaning": top_base2_category["meaning"],
                    "value": 7
                },
                "base3": {
                    "name": top_base3_category["name"],
                    "thai_name": top_base3_category["thai_name"],
                    "meaning": top_base3_category["meaning"],
                    "value": 6
                }
            },
            "pairs": top_pairs,
            "summary": summary,
            "combination_interpretations": top_pairs  # Add this for compatibility with tool_handler
        }
        
        return result
    except Exception as e:
        logging.error(f"Error calculating fortune: {e}")
        raise

def calculate_7n9b_fortune(birthdate_str: str, detail_level: str = "normal") -> Dict[str, Any]:
    """
    Calculate Thai 7-base-9 fortune based on birthdate.
    This is a wrapper for calculate_fortune that accepts a date string instead of a datetime object.
    
    Args:
        birthdate_str: Birthdate in YYYY-MM-DD format
        detail_level: Level of detail (simple, normal, detailed)
        
    Returns:
        Dictionary with fortune calculation results
    """
    try:
        # Parse the birthdate
        if "-" in birthdate_str:
            birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
        elif "/" in birthdate_str:
            # Try to handle different date formats
            if len(birthdate_str.split("/")[0]) == 4:
                # YYYY/MM/DD
                birthdate = datetime.strptime(birthdate_str, "%Y/%m/%d")
            else:
                # DD/MM/YYYY
                birthdate = datetime.strptime(birthdate_str, "%d/%m/%Y")
        else:
            raise ValueError(f"Unsupported date format: {birthdate_str}")
            
        # Call the main calculation function
        return calculate_fortune(birthdate, detail_level)
    except Exception as e:
        logger.error(f"Error in calculate_7n9b_fortune: {e}")
        raise

def process_fortune(message: str) -> Dict[str, Any]:
    """
    Process a fortune request message.
    
    Args:
        message: The message from the user
        
    Returns:
        Dictionary with the fortune calculation results
    """
    try:
        # Placeholder for birthdate analysis
        import re
        
        # Look for a date pattern in the message
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})'   # DD/MM/YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message)
            if match:
                date_str = match.group(1)
                
                # Convert DD/MM/YYYY to YYYY-MM-DD if needed
                if '/' in date_str:
                    day, month, year = date_str.split('/')
                    date_str = f"{year}-{month}-{day}"
                
                # Calculate fortune based on the birthdate
                return calculate_fortune(datetime.datetime.strptime(date_str, "%Y-%m-%d"))
        
        # If no date pattern found, return a message asking for the birthdate
        prompts = [
            "ขอวันเกิดของคุณหน่อยค่ะ (รูปแบบ วัน/เดือน/ปี เช่น 15/01/1990) เพื่อที่จะดูดวงให้ได้แม่นยำค่ะ",
            "อยากรู้วันเกิดของคุณก่อนค่ะ เพื่อจะได้ดูดวงได้แม่นยำ ช่วยบอกในรูปแบบ วัน/เดือน/ปี (เช่น 15/01/1990) นะคะ",
            "ฉันต้องขอวันเกิดของคุณก่อนนะคะ ในรูปแบบ วัน/เดือน/ปี (เช่น 15/01/1990) เพื่อจะได้ดูดวงให้ถูกต้องค่ะ",
            "กรุณาบอกวันเกิดของคุณในรูปแบบ วัน/เดือน/ปี (เช่น 15/01/1990) ค่ะ จะได้ดูดวงให้เหมาะกับคุณค่ะ",
            "ช่วยบอกวันเกิดของคุณในรูปแบบ วัน/เดือน/ปี (เช่น 15/01/1990) หน่อยนะคะ เพื่อจะได้ดูดวงให้ตรงกับชะตาชีวิตของคุณค่ะ"
        ]
        
        import random
        return {"error": True, "message": random.choice(prompts)}
    
    except Exception as e:
        logger.error(f"Error processing fortune request: {e}")
        return {"error": True, "message": f"ดูเหมือนรูปแบบวันเกิดที่คุณบอกจะไม่ตรงตามที่ฉันเข้าใจได้นะคะ 🤔 ช่วยบอกในรูปแบบ วัน/เดือน/ปี (เช่น 15/01/1990) หรือ ปี-เดือน-วัน (เช่น 1990-01-15) ได้ไหมคะ?"} 