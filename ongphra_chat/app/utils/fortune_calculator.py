from datetime import datetime
from typing import Tuple, Dict, List, Any, Optional
import logging
import asyncio
import mysql.connector
from mysql.connector import Error

from app.utils.fortune_tool import calculate_fortune as tool_calculate_fortune
from app.utils.fortune_tool import calculate_7n9b_fortune as tool_calculate_7n9b_fortune

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_thai_zodiac_year_index(year: int) -> int:
    """Determine the Thai zodiac year based on the Gregorian year."""
    return (year - 4) % 12 + 1

def generate_day_values(starting_value: int, total_values: int) -> List[int]:
    """Generate the sequence starting from the given value."""
    values = list(range(1, total_values + 1))
    starting_index = starting_value - 1
    return values[starting_index:] + values[:starting_index]

def get_day_of_week_index(date: datetime) -> int:
    """Get the day of the week with Sunday as 1."""
    return (date.weekday() + 1) % 7 + 1

def get_wrapped_index(index: int, total_values: int) -> int:
    """Wrap the index to ensure it cycles within the total number of values."""
    return ((index - 1) % total_values) + 1

def calculate_sum_base(base_1: List[int], base_2: List[int], base_3: List[int]) -> List[int]:
    """Calculate the sum of values from bases 1, 2, and 3 without wrapping."""
    sum_values = [(base_1[i] + base_2[i] + base_3[i]) for i in range(len(base_1))]
    return sum_values

def generate_data(birth_date_str: str) -> Tuple[List[int], List[int], List[int], List[int]]:
    """Generate fortune data from birth date."""
    try:
        year, month, day = map(int, birth_date_str.split('-'))

        # Convert to Gregorian year if input is in BE
        if year > 2300:
            year -= 543

        birth_date = datetime(year, month, day)
        day_index = get_day_of_week_index(birth_date)
        month_index = birth_date.month
        year = birth_date.year

        # Row 1: Day of the week
        row_1 = generate_day_values(day_index, 7)

        # Row 2: Month with December as the first month, plus 1
        wrapped_month_index = get_wrapped_index(month_index + 1, 12)
        row_2 = generate_day_values(wrapped_month_index, 7)

        # Row 3: Thai zodiac year
        thai_zodiac_year_index = get_thai_zodiac_year_index(year)
        wrapped_zodiac_year_index = get_wrapped_index(thai_zodiac_year_index, 12)
        row_3 = generate_day_values(wrapped_zodiac_year_index, 7)

        # Row 4: Sum of Row 1, Row 2, and Row 3
        row_4 = calculate_sum_base(row_1, row_2, row_3)

        return row_1, row_2, row_3, row_4
    except Exception as e:
        logger.error(f"Error calculating fortune: {str(e)}")
        raise ValueError(f"Error calculating fortune: {str(e)}")

def format_output(row_1: List[int], row_2: List[int], row_3: List[int], row_4: List[int]) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int], List[int]]:
    """Format the output data with Thai labels."""
    day_labels = ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
    month_labels = ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"]
    year_labels = ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]

    base_1 = {label: value for label, value in zip(day_labels, row_1)}
    base_2 = {label: value for label, value in zip(month_labels, row_2)}
    base_3 = {label: value for label, value in zip(year_labels, row_3)}

    return base_1, base_2, base_3, row_4

def calculate_fortune(birthdate_str, detail_level="normal") -> Dict[str, Any]:
    """
    Calculate fortune based on birthdate.
    This is a compatibility function that wraps our new implementation.
    
    Args:
        birthdate_str: Birthdate in string format (YYYY-MM-DD or DD-MM-YYYY)
        detail_level: Level of detail (simple, normal, detailed)
        
    Returns:
        Dictionary with fortune calculation results
    """
    try:
        # Handle different date formats
        if isinstance(birthdate_str, datetime):
            # If it's already a datetime object, use it directly
            return tool_calculate_fortune(birthdate_str, detail_level)
        else:
            # Otherwise treat it as a string
            return tool_calculate_7n9b_fortune(birthdate_str, detail_level)
    except Exception as e:
        logger.error(f"Error in calculate_fortune: {e}")
        raise

def get_category_meanings_dict() -> Dict[str, str]:
    """Return the dictionary of category meanings."""
    return {
        "กดุมภะ": "รายได้รายจ่าย",
        "กัมมะ": "หน้าที่การงาน",
        "ตะนุ": "ตัวท่านเอง",
        "ทาสา": "เหน็จเหนื่อยเพื่อคนอื่น ส่วนรวม",
        "ทาสี": "การเหน็จเหนื่อยเพื่อตัวเอง",
        "ธานัง": "เรื่องเงิน ๆ ทอง ๆ",
        "ปัตนิ": "คู่ครอง",
        "ปิตา": "พ่อหรือผู้ใหญ่ เรื่องนอกบ้าน",
        "ปุตตะ": "เรื่องลูก การเริ่มต้น",
        "พยายะ": "สิ่งไม่ดี เรื่องปิดบัง ซ่อนเร้น",
        "พันธุ": "ญาติพี่น้อง",
        "มรณะ": "เรื่องเจ็บป่วย",
        "มัชฌิมา": "เรื่องกลาง ๆ ไม่หนักหนา",
        "มาตา": "แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว",
        "ลาภะ": "ลาภยศ โชคลาภ",
        "สหัชชะ": "เพื่อนฝูง การติดต่อ",
        "สุภะ": "ความเจริญรุ่งเรือง",
        "หินะ": "ความผิดหวัง",
        "อริ": "ปัญหา อุปสรรค",
        "อัตตะ": "ตัวท่านเอง",
        "โภคา": "สินทรัพย์"
    }

def get_house_types_dict() -> Dict[str, str]:
    """Return the dictionary of house types."""
    return {
        "กดุมภะ": "กาลปักษ์",
        "กัมมะ": "เกณฑ์ชะตา",
        "ตะนุ": "จร",
        "ทาสา": "กาลปักษ์",
        "ทาสี": "เกณฑ์ชะตา",
        "ธานัง": "จร",
        "ปัตนิ": "กาลปักษ์",
        "ปิตา": "เกณฑ์ชะตา",
        "ปุตตะ": "จร",
        "พยายะ": "กาลปักษ์",
        "พันธุ": "เกณฑ์ชะตา",
        "มรณะ": "กาลปักษ์",
        "มัชฌิมา": "กาลปักษ์",
        "มาตา": "เกณฑ์ชะตา",
        "ลาภะ": "จร",
        "สหัชชะ": "กาลปักษ์",
        "สุภะ": "เกณฑ์ชะตา",
        "หินะ": "กาลปักษ์",
        "อริ": "กาลปักษ์",
        "อัตตะ": "กาลปักษ์",
        "โภคา": "จร"
    }

def get_category_meaning(category: str) -> str:
    """Get the meaning for a specific category."""
    meanings = {
        "กดุมภะ": "รายได้รายจ่าย",
        "กัมมะ": "หน้าที่การงาน",
        "ตะนุ": "ตัวท่านเอง",
        "ทาสา": "เหน็จเหนื่อยเพื่อคนอื่น ส่วนรวม",
        "ทาสี": "การเหน็จเหนื่อยเพื่อตัวเอง",
        "ธานัง": "เรื่องเงิน ๆ ทอง ๆ",
        "ปัตนิ": "คู่ครอง",
        "ปิตา": "พ่อหรือผู้ใหญ่ เรื่องนอกบ้าน",
        "ปุตตะ": "เรื่องลูก การเริ่มต้น",
        "พยายะ": "สิ่งไม่ดี เรื่องปิดบัง ซ่อนเร้น",
        "พันธุ": "ญาติพี่น้อง",
        "มรณะ": "เรื่องเจ็บป่วย",
        "มัชฌิมา": "เรื่องกลาง ๆ ไม่หนักหนา",
        "มาตา": "แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว",
        "ลาภะ": "ลาภยศ โชคลาภ",
        "สหัชชะ": "เพื่อนฝูง การติดต่อ",
        "สุภะ": "ความเจริญรุ่งเรือง",
        "หินะ": "ความผิดหวัง",
        "อริ": "ปัญหา อุปสรรค",
        "อัตตะ": "ตัวท่านเอง",
        "โภคา": "สินทรัพย์"
    }
    return meanings.get(category, "ไม่พบความหมาย")

def get_house_type(category: str) -> str:
    """Get the house type for a specific category."""
    house_types = {
        "กดุมภะ": "กาลปักษ์",
        "กัมมะ": "เกณฑ์ชะตา",
        "ตะนุ": "จร",
        "ทาสา": "กาลปักษ์",
        "ทาสี": "เกณฑ์ชะตา",
        "ธานัง": "จร",
        "ปัตนิ": "กาลปักษ์",
        "ปิตา": "เกณฑ์ชะตา",
        "ปุตตะ": "จร",
        "พยายะ": "กาลปักษ์",
        "พันธุ": "เกณฑ์ชะตา",
        "มรณะ": "กาลปักษ์",
        "มัชฌิมา": "กาลปักษ์",
        "มาตา": "เกณฑ์ชะตา",
        "ลาภะ": "จร",
        "สหัชชะ": "กาลปักษ์",
        "สุภะ": "เกณฑ์ชะตา",
        "หินะ": "กาลปักษ์",
        "อริ": "กาลปักษ์",
        "อัตตะ": "กาลปักษ์",
        "โภคา": "จร"
    }
    return house_types.get(category, "ไม่ทราบ")

def determine_influence(category: str) -> str:
    """Determine the influence type based on house type."""
    house_type = get_house_type(category)
    
    if house_type == "กาลปักษ์":
        return "ดี"
    elif house_type == "เกณฑ์ชะตา":
        return "กลาง"
    elif house_type == "จร":
        return "กลาง"
    else:
        return "เดิม"

def determine_combined_influence(category1: str, category2: str) -> str:
    """Determine the combined influence of two categories."""
    influence1 = determine_influence(category1)
    influence2 = determine_influence(category2)
    
    # Rules for combining influences
    if influence1 == "ดี" and influence2 == "ดี":
        return "ดี"
    elif influence1 == "ร้าย" and influence2 == "ร้าย":
        return "ร้าย"
    elif "ดี" in [influence1, influence2] and "ร้าย" in [influence1, influence2]:
        return "กลาง"
    elif "ดี" in [influence1, influence2]:
        return "ดี"
    elif "ร้าย" in [influence1, influence2]:
        return "กลาง"
    else:
        return "กลาง"

def generate_heading_for_combination(cat1: str, cat2: str, value1: int, value2: int) -> str:
    """Generate a heading for a category combination based on their values and meanings."""
    cat1_meaning = get_category_meaning(cat1)
    cat2_meaning = get_category_meaning(cat2)
    
    # If both values are high (5-7)
    if value1 >= 5 and value2 >= 5:
        return f"ความสัมพันธ์ที่แข็งแกร่งระหว่าง{cat1}และ{cat2}"
    
    # If one value is high and one is low
    elif (value1 >= 5 and value2 <= 3) or (value1 <= 3 and value2 >= 5):
        high_cat = cat1 if value1 > value2 else cat2
        low_cat = cat2 if value1 > value2 else cat1
        return f"อิทธิพลของ{high_cat}ที่ส่งผลต่อ{low_cat}"
    
    # If both values are moderate (3-4)
    elif 3 <= value1 <= 4 and 3 <= value2 <= 4:
        return f"ความสมดุลระหว่าง{cat1}และ{cat2}"
    
    # If both values are low (1-2)
    elif value1 <= 2 and value2 <= 2:
        return f"การขาดอิทธิพลของ{cat1}และ{cat2}"
    
    # Default case
    else:
        return f"ความเชื่อมโยงระหว่าง{cat1}และ{cat2}"

def generate_meaning_for_combination(cat1: str, cat2: str, cat1_meaning: str, cat2_meaning: str, value1: int, value2: int) -> str:
    """Generate a meaning for a category combination based on their values and meanings."""
    # Common prefixes based on values
    strong_prefix = "มีอิทธิพลอย่างมากในเรื่อง"
    moderate_prefix = "มีความสำคัญพอสมควรในเรื่อง"
    weak_prefix = "มีผลกระทบเพียงเล็กน้อยในเรื่อง"
    
    # Generate descriptions based on values
    if value1 >= 6:
        cat1_desc = f"{cat1}({cat1_meaning}) {strong_prefix}ชีวิตของคุณ"
    elif 4 <= value1 <= 5:
        cat1_desc = f"{cat1}({cat1_meaning}) {moderate_prefix}ชีวิตของคุณ"
    else:
        cat1_desc = f"{cat1}({cat1_meaning}) {weak_prefix}ชีวิตของคุณ"
        
    if value2 >= 6:
        cat2_desc = f"{cat2}({cat2_meaning}) {strong_prefix}ชีวิตของคุณเช่นกัน"
    elif 4 <= value2 <= 5:
        cat2_desc = f"{cat2}({cat2_meaning}) {moderate_prefix}ชีวิตของคุณเช่นกัน"
    else:
        cat2_desc = f"{cat2}({cat2_meaning}) {weak_prefix}ชีวิตของคุณเช่นกัน"
    
    # Combined meaning
    combined_meaning = f"{cat1_desc} และ{cat2_desc} "
    
    # Additional interpretation based on specific combinations
    if "ธานัง" in [cat1, cat2] and "กดุมภะ" in [cat1, cat2]:
        if value1 >= 5 and value2 >= 5:
            combined_meaning += "ทำให้คุณมีโอกาสที่ดีในการสร้างความมั่นคงทางการเงิน การลงทุนจะให้ผลตอบแทนที่ดี"
        else:
            combined_meaning += "แสดงว่าเรื่องการเงินและรายได้มีความสำคัญแต่อาจไม่ใช่ประเด็นหลักในชีวิตคุณ"
    
    elif "อัตตะ" in [cat1, cat2] and "ตะนุ" in [cat1, cat2]:
        if value1 >= 5 and value2 >= 5:
            combined_meaning += "แสดงถึงความมั่นใจในตัวเองสูงและมีเอกลักษณ์เฉพาะตัวที่โดดเด่น"
        else:
            combined_meaning += "แสดงว่าคุณอาจยังไม่มั่นใจในตัวเองเท่าที่ควรหรือกำลังค้นหาตัวตนที่แท้จริง"
    
    elif "พยายะ" in [cat1, cat2]:
        if value1 >= 5 or value2 >= 5:
            combined_meaning += "ทำให้คุณต้องระวังเรื่องซ่อนเร้นหรือปัญหาที่อาจเกิดขึ้นโดยไม่คาดคิด"
        else:
            combined_meaning += "แสดงว่าคุณไม่ค่อยมีปัญหาเรื่องความลับหรือเรื่องปิดบัง"
    
    else:
        # Generic combination meaning
        if value1 + value2 >= 10:
            combined_meaning += "ทำให้เห็นว่าสองด้านนี้มีความสำคัญมากในชีวิตของคุณในช่วงนี้"
        elif 6 <= value1 + value2 <= 9:
            combined_meaning += "แสดงให้เห็นว่าสองด้านนี้มีความสำคัญพอสมควรในชีวิตของคุณ"
        else:
            combined_meaning += "แสดงว่าสองด้านนี้ไม่ค่อยส่งผลกระทบมากนักต่อชีวิตของคุณ"
    
    return combined_meaning

# Database functions for fetching interpretations
def get_db_connection(db_config):
    """Create database connection"""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None

def get_category_interpretations(category1: str, category2: str, category3: str = None, db_config: Dict = None) -> List[Dict]:
    """Get interpretations from database based on categories combination."""
    if not db_config:
        # Use default configuration if not provided
        db_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'fortune_user',
            'password': 'fortune_password',
            'database': 'fortune_db'
        }
    
    interpretations = []
    connection = get_db_connection(db_config)
    
    if not connection:
        logging.error("Cannot connect to database")
        return interpretations
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Generate file name format based on categories
        if category3:
            file_name = f"{category1}-{category2}-{category3}"
        else:
            file_name = f"{category1}-{category2}"
        
        # Query for exact match
        query = """
        SELECT cc.id as combination_id, r.heading, r.meaning, r.influence_type
        FROM category_combinations cc
        JOIN readings r ON cc.id = r.combination_id
        WHERE cc.file_name = %s
        """
        cursor.execute(query, (file_name,))
        results = cursor.fetchall()
        
        if results:
            interpretations.extend(results)
        else:
            # If exact match not found, try partial match
            logging.info(f"No exact match found for {file_name}, trying partial match")
            
            # Query categories IDs
            cursor.execute("SELECT id, name FROM categories WHERE name IN (%s, %s, %s)", 
                           (category1, category2, category3 if category3 else ""))
            category_ids = {}
            for row in cursor.fetchall():
                category_ids[row['name']] = row['id']
            
            if category1 in category_ids and category2 in category_ids:
                # Query for partial match
                query = """
                SELECT cc.id as combination_id, r.heading, r.meaning, r.influence_type
                FROM category_combinations cc
                JOIN readings r ON cc.id = r.combination_id
                WHERE (cc.category1_id = %s AND cc.category2_id = %s)
                   OR (cc.category1_id = %s AND cc.category2_id = %s)
                """
                params = (category_ids[category1], category_ids[category2], 
                          category_ids[category2], category_ids[category1])
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                interpretations.extend(results)
        
        cursor.close()
    except Error as e:
        logging.error(f"Database error: {e}")
    finally:
        connection.close()
    
    return interpretations

def get_all_interpretations_for_bases(base1: Dict[str, int], base2: Dict[str, int], base3: Dict[str, int], db_config: Dict = None) -> List[Dict]:
    """Get all interpretations for all category combinations across bases."""
    # Get all categories from each base
    base1_categories = list(base1.keys())
    base2_categories = list(base2.keys())
    base3_categories = list(base3.keys())
    
    # Create a list to store all combination interpretations
    combination_interpretations = []
    
    # Process all combinations between base1 and base2
    for cat1 in base1_categories:
        for cat2 in base2_categories:
            # Query database for this combination
            db_interpretations = get_category_interpretations(cat1, cat2, None, db_config)
            
            # If found in database, add them
            if db_interpretations:
                for interp in db_interpretations:
                    combination_interpretations.append({
                        "category": f"{cat1}-{cat2}",
                        "heading": interp.get("heading", f"อิทธิพลของ {cat1} และ {cat2}"),
                        "meaning": interp.get("meaning", "ไม่พบรายละเอียดการตีความ"),
                        "influence": interp.get("influence_type", "กลาง")
                    })
            else:
                # Create fallback interpretation based on meanings and values
                cat1_meaning = get_category_meaning(cat1)
                cat2_meaning = get_category_meaning(cat2)
                cat1_value = base1[cat1]
                cat2_value = base2[cat2]
                
                # Determine combined influence
                influence = determine_combined_influence(cat1, cat2)
                
                # Generate heading and meaning based on values
                heading = generate_heading_for_combination(cat1, cat2, cat1_value, cat2_value)
                meaning = generate_meaning_for_combination(cat1, cat2, cat1_meaning, cat2_meaning, cat1_value, cat2_value)
                
                combination_interpretations.append({
                    "category": f"{cat1}-{cat2}",
                    "heading": heading,
                    "meaning": meaning,
                    "influence": influence
                })
    
    # Process all combinations between base1 and base3
    for cat1 in base1_categories:
        for cat3 in base3_categories:
            # Query database for this combination
            db_interpretations = get_category_interpretations(cat1, cat3, None, db_config)
            
            # If found in database, add them
            if db_interpretations:
                for interp in db_interpretations:
                    combination_interpretations.append({
                        "category": f"{cat1}-{cat3}",
                        "heading": interp.get("heading", f"อิทธิพลของ {cat1} และ {cat3}"),
                        "meaning": interp.get("meaning", "ไม่พบรายละเอียดการตีความ"),
                        "influence": interp.get("influence_type", "กลาง")
                    })
            else:
                # Create fallback interpretation
                cat1_meaning = get_category_meaning(cat1)
                cat3_meaning = get_category_meaning(cat3)
                cat1_value = base1[cat1]
                cat3_value = base3[cat3]
                
                influence = determine_combined_influence(cat1, cat3)
                heading = generate_heading_for_combination(cat1, cat3, cat1_value, cat3_value)
                meaning = generate_meaning_for_combination(cat1, cat3, cat1_meaning, cat3_meaning, cat1_value, cat3_value)
                
                combination_interpretations.append({
                    "category": f"{cat1}-{cat3}",
                    "heading": heading,
                    "meaning": meaning,
                    "influence": influence
                })
    
    # Process all combinations between base2 and base3
    for cat2 in base2_categories:
        for cat3 in base3_categories:
            # Query database for this combination
            db_interpretations = get_category_interpretations(cat2, cat3, None, db_config)
            
            # If found in database, add them
            if db_interpretations:
                for interp in db_interpretations:
                    combination_interpretations.append({
                        "category": f"{cat2}-{cat3}",
                        "heading": interp.get("heading", f"อิทธิพลของ {cat2} และ {cat3}"),
                        "meaning": interp.get("meaning", "ไม่พบรายละเอียดการตีความ"),
                        "influence": interp.get("influence_type", "กลาง")
                    })
            else:
                # Create fallback interpretation
                cat2_meaning = get_category_meaning(cat2)
                cat3_meaning = get_category_meaning(cat3)
                cat2_value = base2[cat2]
                cat3_value = base3[cat3]
                
                influence = determine_combined_influence(cat2, cat3)
                heading = generate_heading_for_combination(cat2, cat3, cat2_value, cat3_value)
                meaning = generate_meaning_for_combination(cat2, cat3, cat2_meaning, cat3_meaning, cat2_value, cat3_value)
                
                combination_interpretations.append({
                    "category": f"{cat2}-{cat3}",
                    "heading": heading,
                    "meaning": meaning,
                    "influence": influence
                })
    
    # Sort combinations by the sum of their values (higher first)
    def get_combination_value(combination):
        cats = combination["category"].split("-")
        if len(cats) != 2:
            return 0
            
        cat1, cat2 = cats
        value1 = 0
        value2 = 0
        
        if cat1 in base1:
            value1 = base1[cat1]
        elif cat1 in base2:
            value1 = base2[cat1]
        elif cat1 in base3:
            value1 = base3[cat1]
            
        if cat2 in base1:
            value2 = base1[cat2]
        elif cat2 in base2:
            value2 = base2[cat2]
        elif cat2 in base3:
            value2 = base3[cat2]
            
        return value1 + value2
    
    # Sort combinations by their combined value (higher values first)
    combination_interpretations.sort(key=get_combination_value, reverse=True)
    
    return combination_interpretations

def enrich_fortune_calculation(fortune_data: Dict[str, Any], db_config: Dict = None) -> Dict[str, Any]:
    """Enrich fortune calculation with interpretations from database."""
    enriched_data = fortune_data.copy()
    
    # Get detailed interpretations for all category combinations
    combination_interpretations = get_all_interpretations_for_bases(
        fortune_data["base1"], 
        fortune_data["base2"], 
        fortune_data["base3"],
        db_config
    )
    
    # Add combination interpretations to the result
    enriched_data["combination_interpretations"] = combination_interpretations
    
    # Generate a summary from the most significant interpretations
    # Sort by influence type and combined value
    influence_order = {"ดี": 0, "กลาง": 1, "เดิม": 2, "ร้าย": 3}
    
    # Get top combinations (highest combined values)
    top_interpretations = combination_interpretations[:5] if len(combination_interpretations) >= 5 else combination_interpretations
    
    # Further sort by influence (ดี first)
    top_interpretations = sorted(
        top_interpretations, 
        key=lambda x: influence_order.get(x.get("influence", "เดิม"), 4)
    )
    
    # Get top 3 for summary
    summary_interpretations = top_interpretations[:3]
    
    if summary_interpretations:
        # Extract the highest values from each base for context
        highest_base1 = max(fortune_data["base1"].items(), key=lambda x: x[1])
        highest_base2 = max(fortune_data["base2"].items(), key=lambda x: x[1])
        highest_base3 = max(fortune_data["base3"].items(), key=lambda x: x[1])
        
        # Create context string with the highest values
        context = f"จากวันเกิดของคุณ พบว่าฐานหลักที่มีอิทธิพลสูงสุดคือ "
        context += f"{highest_base1[0]} ({highest_base1[1]}), "
        context += f"{highest_base2[0]} ({highest_base2[1]}), และ"
        context += f"{highest_base3[0]} ({highest_base3[1]}) "
        
        # Add meaning context
        meaning_context = f"ซึ่งเกี่ยวข้องกับ{get_category_meaning(highest_base1[0])}, "
        meaning_context += f"{get_category_meaning(highest_base2[0])}, และ"
        meaning_context += f"{get_category_meaning(highest_base3[0])} "
        
        # Combine with top interpretations
        interpretation_summary = []
        for interp in summary_interpretations:
            interpretation_summary.append(interp.get("heading", ""))
        
        # Build final summary
        summary = context + meaning_context + "\n\n"
        if interpretation_summary:
            summary += "การตีความที่สำคัญ:\n- " + "\n- ".join(interpretation_summary)
        
        enriched_data["summary"] = summary
    else:
        # Generate basic summary if no interpretations found
        enriched_data["summary"] = "ไม่พบการตีความที่เฉพาะเจาะจง กรุณาปรึกษาโหราจารย์ผู้เชี่ยวชาญ"
    
    # Also include individual category interpretations
    individual_interpretations = []
    for base_name, categories in [("base1", fortune_data["base1"]), 
                                 ("base2", fortune_data["base2"]), 
                                 ("base3", fortune_data["base3"])]:
        for category, value in categories.items():
            meaning = get_category_meaning(category)
            influence = determine_influence(category)
            
            individual_interpretations.append({
                "category": category,
                "meaning": meaning,
                "influence": influence,
                "value": value,
                "heading": f"ระดับอิทธิพลของ{category}: {value}",
                "detail": generate_category_detail(category, meaning, value)
            })
    
    # Sort individual interpretations by value (highest first)
    individual_interpretations.sort(key=lambda x: x["value"], reverse=True)
    
    # Add to enriched data
    enriched_data["individual_interpretations"] = individual_interpretations
    
    return enriched_data

def generate_category_detail(category: str, meaning: str, value: int) -> str:
    """Generate detailed interpretation for a single category based on its value."""
    prefix = f"{category}({meaning}) "
    
    if value >= 6:
        return f"{prefix}มีอิทธิพลสูงในชีวิตคุณ เรื่องนี้มีความสำคัญมากในช่วงนี้"
    elif 4 <= value <= 5:
        return f"{prefix}มีอิทธิพลปานกลางค่อนข้างสูงในชีวิตคุณ เรื่องนี้มีความสำคัญพอสมควร"
    elif 2 <= value <= 3:
        return f"{prefix}มีอิทธิพลค่อนข้างน้อยในชีวิตคุณ เรื่องนี้ไม่ค่อยส่งผลกระทบมากนัก"
    else:
        return f"{prefix}แทบไม่มีอิทธิพลในชีวิตคุณ เรื่องนี้ไม่ค่อยสำคัญในช่วงนี้"