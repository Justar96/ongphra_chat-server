from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Define the fortune tool schema
FORTUNE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_7n9b_fortune",
        "description": "คำนวณดวงชะตาตามศาสตร์ไทย 7 ฐาน 9 จากวันเดือนปีเกิด แล้วแปลผลอย่างละเอียด",
        "parameters": {
            "type": "object",
            "properties": {
                "birthdate": {
                    "type": "string",
                    "description": "วันเกิดในรูปแบบ YYYY-MM-DD (เช่น 1990-05-15)"
                }
            },
            "required": ["birthdate"]
        }
    }
}

# Constants for 7N9B interpretation
BASE1_LABELS = ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
BASE2_LABELS = ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"]
BASE3_LABELS = ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]

CATEGORY_MEANINGS = {
    "อัตตะ": "ตัวท่านเอง",
    "หินะ": "ความผิดหวัง",
    "ธานัง": "เรื่องเงิน ๆ ทอง ๆ",
    "ปิตา": "พ่อหรือผู้ใหญ่ เรื่องนอกบ้าน",
    "มาตา": "แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว",
    "โภคา": "สินทรัพย์",
    "มัชฌิมา": "เรื่องกลาง ๆ ไม่หนักหนา",
    "ตะนุ": "ตัวท่านเอง",
    "กดุมภะ": "รายได้รายจ่าย",
    "สหัชชะ": "เพื่อนฝูง การติดต่อ",
    "พันธุ": "ญาติพี่น้อง",
    "ปุตตะ": "เรื่องลูก การเริ่มต้น",
    "อริ": "ปัญหา อุปสรรค",
    "ปัตนิ": "คู่ครอง",
    "มรณะ": "เรื่องเจ็บป่วย",
    "สุภะ": "ความเจริญรุ่งเรือง",
    "กัมมะ": "หน้าที่การงาน",
    "ลาภะ": "ลาภยศ โชคลาภ",
    "พยายะ": "สิ่งไม่ดี เรื่องปิดบัง ซ่อนเร้น",
    "ทาสา": "เหน็จเหนื่อยเพื่อคนอื่น ส่วนรวม",
    "ทาสี": "การเหน็จเหนื่อยเพื่อตัวเอง"
}

HOUSE_TYPES = {
    "อัตตะ": "กาลปักษ์",
    "หินะ": "กาลปักษ์",
    "ธานัง": "จร",
    "ปิตา": "เกณฑ์ชะตา",
    "มาตา": "เกณฑ์ชะตา",
    "โภคา": "จร",
    "มัชฌิมา": "กาลปักษ์",
    "ตะนุ": "จร",
    "กดุมภะ": "กาลปักษ์",
    "สหัชชะ": "กาลปักษ์",
    "พันธุ": "เกณฑ์ชะตา",
    "ปุตตะ": "จร",
    "อริ": "กาลปักษ์",
    "ปัตนิ": "กาลปักษ์",
    "มรณะ": "กาลปักษ์",
    "สุภะ": "เกณฑ์ชะตา",
    "กัมมะ": "เกณฑ์ชะตา",
    "ลาภะ": "จร",
    "พยายะ": "กาลปักษ์",
    "ทาสา": "กาลปักษ์",
    "ทาสี": "เกณฑ์ชะตา"
}

def get_category_meaning(category: str) -> str:
    """Get the meaning for a specific category."""
    return CATEGORY_MEANINGS.get(category, "ไม่พบความหมาย")

def get_house_type(category: str) -> str:
    """Get the house type for a specific category."""
    return HOUSE_TYPES.get(category, "ไม่ทราบ")

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

def get_day_of_week_index(date: datetime) -> int:
    """Get the day of the week with Sunday as 1."""
    return (date.weekday() + 1) % 7 + 1

def get_wrapped_index(index: int, total_values: int) -> int:
    """Wrap the index to ensure it cycles within the total number of values."""
    return ((index - 1) % total_values) + 1

def generate_day_values(starting_value: int, total_values: int) -> List[int]:
    """Generate the sequence starting from the given value."""
    values = list(range(1, total_values + 1))
    starting_index = starting_value - 1
    return values[starting_index:] + values[:starting_index]

def get_thai_zodiac_year_index(year: int) -> int:
    """Determine the Thai zodiac year based on the Gregorian year."""
    return (year - 4) % 12 + 1

def calculate_fortune(birthdate_str: str) -> Dict[str, Any]:
    """Calculate Thai fortune (7N9B) based on birthdate."""
    try:
        # Parse the birthdate
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
        year = birthdate.year
        
        # Convert to Gregorian year if input is in BE
        if year > 2300:
            year -= 543
            
        # Get day of week index (Sunday = 1)
        day_index = get_day_of_week_index(birthdate)
        
        # Get month index with December + 1 wrapping
        month_index = get_wrapped_index(birthdate.month + 1, 12)
        
        # Get Thai zodiac year index
        thai_zodiac_year_index = get_thai_zodiac_year_index(year)
        zodiac_index = get_wrapped_index(thai_zodiac_year_index, 12)
        
        # Generate base values
        base1_values = generate_day_values(day_index, 7)
        base2_values = generate_day_values(month_index, 7)
        base3_values = generate_day_values(zodiac_index, 7)
        
        # Calculate base4 (sum of bases 1-3)
        base4_values = [base1_values[i] + base2_values[i] + base3_values[i] for i in range(7)]
        
        # Create labeled bases
        base1 = {label: value for label, value in zip(BASE1_LABELS, base1_values)}
        base2 = {label: value for label, value in zip(BASE2_LABELS, base2_values)}
        base3 = {label: value for label, value in zip(BASE3_LABELS, base3_values)}
        
        # Get top categories from each base
        top_base1 = max(base1.items(), key=lambda x: x[1])
        top_base2 = max(base2.items(), key=lambda x: x[1])
        top_base3 = max(base3.items(), key=lambda x: x[1])
        
        # Generate individual interpretations
        individual_interpretations = []
        for base_name, categories in [("base1", base1), ("base2", base2), ("base3", base3)]:
            for category, value in categories.items():
                meaning = get_category_meaning(category)
                influence = determine_influence(category)
                
                individual_interpretations.append({
                    "category": category,
                    "meaning": meaning,
                    "influence": influence,
                    "value": value,
                    "heading": f"ระดับอิทธิพลของ{category}: {value}",
                    "detail": f"{category}({meaning}) มีอิทธิพล{influence}ในชีวิตคุณ ระดับคะแนน {value}"
                })
        
        # Sort interpretations by value in descending order
        individual_interpretations.sort(key=lambda x: x["value"], reverse=True)
        
        # Generate combination interpretations for top categories
        combination_interpretations = []
        top_categories = [top_base1[0], top_base2[0], top_base3[0]]
        
        # Add combinations between top categories
        for i in range(len(top_categories)):
            for j in range(i+1, len(top_categories)):
                cat1 = top_categories[i]
                cat2 = top_categories[j]
                val1 = max(base1.get(cat1, 0), base2.get(cat1, 0), base3.get(cat1, 0))
                val2 = max(base1.get(cat2, 0), base2.get(cat2, 0), base3.get(cat2, 0))
                
                # Generate heading and meaning
                if (cat1 == "ธานัง" and cat2 == "กดุมภะ") or (cat1 == "กดุมภะ" and cat2 == "ธานัง"):
                    heading = "การเงินและรายได้"
                    meaning = "เงินทองและรายได้เป็นจุดเด่นในชีวิตคุณ มีโอกาสที่ดีในการสร้างความมั่นคงทางการเงิน การลงทุนมีแนวโน้มให้ผลตอบแทนที่ดี"
                elif (cat1 == "ลาภะ" and cat2 == "ธานัง") or (cat1 == "ธานัง" and cat2 == "ลาภะ"):
                    heading = "โชคลาภทางการเงิน"
                    meaning = "คุณมีดวงดีในเรื่องการเงินและโชคลาภ มีโอกาสได้รับทรัพย์จากหลายทางทั้งจากการงานและโชค"
                else:
                    heading = f"ความสัมพันธ์ระหว่าง{cat1}และ{cat2}"
                    meaning = (f"อิทธิพลของ{cat1}({get_category_meaning(cat1)}) "
                            f"และ{cat2}({get_category_meaning(cat2)}) "
                            f"มีผลต่อชีวิตคุณในระดับสูง ควรให้ความสำคัญกับความสมดุลระหว่างสองด้านนี้")
                
                combination_interpretations.append({
                    "category": f"{cat1}-{cat2}",
                    "heading": heading,
                    "meaning": meaning,
                    "influence": determine_combined_influence(cat1, cat2)
                })
        
        # Create summary focusing on the top 3 highest values across all bases
        all_values = [(category, value, get_category_meaning(category)) 
                    for base in [base1, base2, base3] 
                    for category, value in base.items()]
        all_values.sort(key=lambda x: x[1], reverse=True)
        top_three = all_values[:3]
        
        summary = (
            f"จากวันเกิดของคุณ พบว่าฐานหลักที่มีอิทธิพลสูงสุดคือ "
            f"{top_three[0][0]} ({top_three[0][1]}), "
            f"{top_three[1][0]} ({top_three[1][1]}), และ "
            f"{top_three[2][0]} ({top_three[2][1]}) "
            f"ซึ่งเกี่ยวข้องกับ{top_three[0][2]}, "
            f"{top_three[1][2]}, และ "
            f"{top_three[2][2]}"
        )
        
        return {
            "bases": {
                "base1": base1,
                "base2": base2,
                "base3": base3,
                "base4": base4_values
            },
            "individual_interpretations": individual_interpretations,
            "combination_interpretations": combination_interpretations,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error calculating fortune: {str(e)}")
        raise ValueError(f"ไม่สามารถคำนวณดวงชะตาได้: {str(e)}")

def calculate_7n9b_fortune(birthdate: str) -> Dict[str, Any]:
    """Tool function to calculate Thai 7N9B fortune from birthdate."""
    try:
        # Validate the birthdate format
        datetime.strptime(birthdate, "%Y-%m-%d")
        
        # Calculate fortune
        fortune_result = calculate_fortune(birthdate)
        return fortune_result
    except ValueError as e:
        raise ValueError(f"รูปแบบวันเกิดไม่ถูกต้อง ต้องเป็น YYYY-MM-DD: {str(e)}")
    except Exception as e:
        logger.error(f"Error in fortune calculation: {str(e)}")
        raise ValueError(f"เกิดข้อผิดพลาดในการคำนวณดวงชะตา: {str(e)}") 