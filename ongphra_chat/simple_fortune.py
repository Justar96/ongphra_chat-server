from datetime import datetime
import json

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

def get_day_of_week_index(date):
    """Get the day of the week with Sunday as 1."""
    return (date.weekday() + 1) % 7 + 1

def get_wrapped_index(index, total_values):
    """Wrap the index to ensure it cycles within the total number of values."""
    return ((index - 1) % total_values) + 1

def generate_day_values(starting_value, total_values):
    """Generate the sequence starting from the given value."""
    values = list(range(1, total_values + 1))
    starting_index = starting_value - 1
    return values[starting_index:] + values[:starting_index]

def get_thai_zodiac_year_index(year):
    """Determine the Thai zodiac year based on the Gregorian year."""
    return (year - 4) % 12 + 1

def calculate_fortune(birthdate_str):
    """Calculate Thai fortune (7N9B) based on birthdate."""
    try:
        # Parse the birthdate
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
        year = birthdate.year
        
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
        
        # Create summary focusing on the top 3 highest values across all bases
        all_values = [(category, value, CATEGORY_MEANINGS.get(category, "")) 
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
            "birthdate": birthdate_str,
            "day_of_week": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][birthdate.weekday()],
            "thai_zodiac_year": thai_zodiac_year_index,
            "bases": {
                "base1": base1,
                "base2": base2,
                "base3": base3,
                "base4": base4_values
            },
            "top_categories": {
                "base1": top_base1,
                "base2": top_base2,
                "base3": top_base3
            },
            "summary": summary
        }
        
    except Exception as e:
        print(f"Error calculating fortune: {str(e)}")
        return {"error": str(e)}

# Convert DD-MM-YYYY to YYYY-MM-DD
def convert_date_format(date_str):
    """Convert a date from DD-MM-YYYY format to YYYY-MM-DD."""
    try:
        day, month, year = date_str.split("-")
        return f"{year}-{month}-{day}"
    except:
        return date_str

# Main script
if __name__ == "__main__":
    input_date = "14-02-1996"  # DD-MM-YYYY format
    print(f"Input birthdate: {input_date}")
    
    # Convert to YYYY-MM-DD
    formatted_date = convert_date_format(input_date)
    print(f"Formatted birthdate: {formatted_date}")
    
    # Calculate fortune
    fortune_result = calculate_fortune(formatted_date)
    
    # Print the result
    print("\n=== Fortune Calculation ===")
    print(json.dumps(fortune_result, indent=2, ensure_ascii=False))
    
    # Print bases summary
    print("\n=== Bases ===")
    for base_name, base_data in fortune_result["bases"].items():
        if isinstance(base_data, dict):
            print(f"{base_name}:")
            for category, value in base_data.items():
                meaning = CATEGORY_MEANINGS.get(category, "")
                print(f"  {category} ({meaning}): {value}")
        else:
            print(f"{base_name}: {base_data}")
    
    # Print top categories
    print("\n=== Top Categories ===")
    for base_name, (category, value) in fortune_result["top_categories"].items():
        meaning = CATEGORY_MEANINGS.get(category, "")
        print(f"{base_name}: {category} ({meaning}) = {value}")
    
    # Print summary
    print("\n=== Summary ===")
    print(fortune_result["summary"]) 