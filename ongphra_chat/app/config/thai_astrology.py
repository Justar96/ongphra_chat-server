# app/config/thai_astrology.py
"""Configuration file for Thai astrological constants and mappings"""

from typing import Dict, List, Any

# Thai zodiac animal mappings
ZODIAC_ANIMALS = {
    "ชวด": 1,  # Rat
    "ฉลู": 2,  # Ox
    "ขาล": 3,  # Tiger
    "เถาะ": 4,  # Rabbit
    "มะโรง": 5,  # Dragon
    "มะเส็ง": 6,  # Snake
    "มะเมีย": 7,  # Horse
    "มะแม": 8,  # Goat
    "วอก": 9,  # Monkey
    "ระกา": 10,  # Rooster
    "จอ": 11,  # Dog
    "กุน": 12,  # Pig
}

# Mapping from index to zodiac animal name
ZODIAC_INDEX_TO_ANIMAL = {
    1: 'ชวด',    # Rat
    2: 'ฉลู',     # Ox
    3: 'ขาล',     # Tiger
    4: 'เถาะ',    # Rabbit
    5: 'มะโรง',   # Dragon
    6: 'มะเส็ง',  # Snake
    7: 'มะเมีย',  # Horse
    8: 'มะแม',    # Goat
    9: 'วอก',     # Monkey
    10: 'ระกา',   # Rooster
    11: 'จอ',     # Dog
    12: 'กุน'     # Pig
}

# Thai day of week values
DAY_VALUES = {
    "อาทิตย์": 1,  # Sunday
    "จันทร์": 2,  # Monday
    "อังคาร": 3,  # Tuesday
    "พุธ": 4,  # Wednesday
    "พฤหัสบดี": 5,  # Thursday
    "ศุกร์": 6,  # Friday
    "เสาร์": 7,  # Saturday
}

# Mapping from day index to Thai day name
DAY_INDEX_TO_NAME = {v: k for k, v in DAY_VALUES.items()}

# Thai position labels for each base
DAY_LABELS = ["อัตตะ", "หินะ", "ธานัง", "ปิตา", "มาตา", "โภคา", "มัชฌิมา"]
MONTH_LABELS = ["ตะนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ"]
YEAR_LABELS = ["มรณะ", "สุภะ", "กัมมะ", "ลาภะ", "พยายะ", "ทาสา", "ทาสี"]

# Category mappings with Thai meanings, house numbers, and house types
CATEGORY_MAPPINGS = {
    'กดุมภะ': {'thai_meaning': 'รายได้รายจ่าย', 'house_number': 1, 'house_type': 'กาลปักษ์'},
    'กัมมะ': {'thai_meaning': 'หน้าที่การงาน', 'house_number': 2, 'house_type': 'เกณฑ์ชะตา'},
    'ตะนุ': {'thai_meaning': 'ตัวท่านเอง', 'house_number': 3, 'house_type': 'จร'},
    'ทาสา': {'thai_meaning': 'เหน็จเหนื่อยเพื่อคนอื่น ส่วนรวม', 'house_number': 4, 'house_type': 'กาลปักษ์'},
    'ทาสี': {'thai_meaning': 'การเหน็จเหนื่อยเพื่อตัวเอง', 'house_number': 5, 'house_type': 'เกณฑ์ชะตา'},
    'ธานัง': {'thai_meaning': 'เรื่องเงิน ๆ ทอง ๆ', 'house_number': 6, 'house_type': 'จร'},
    'ปัตนิ': {'thai_meaning': 'คู่ครอง', 'house_number': 7, 'house_type': 'กาลปักษ์'},
    'ปิตา': {'thai_meaning': 'พ่อหรือผู้ใหญ่ เรื่องนอกบ้าน', 'house_number': 8, 'house_type': 'เกณฑ์ชะตา'},
    'ปุตตะ': {'thai_meaning': 'เรื่องลูก การเริ่มต้น', 'house_number': 9, 'house_type': 'จร'},
    'พยายะ': {'thai_meaning': 'สิ่งไม่ดี เรื่องปิดบัง ซ่อนเร้น', 'house_number': 10, 'house_type': 'กาลปักษ์'},
    'พันธุ': {'thai_meaning': 'ญาติพี่น้อง', 'house_number': 11, 'house_type': 'เกณฑ์ชะตา'},
    'มรณะ': {'thai_meaning': 'เรื่องเจ็บป่วย', 'house_number': 12, 'house_type': 'กาลปักษ์'},
    'มัชฌิมา': {'thai_meaning': 'เรื่องกลาง ๆ ไม่หนักหนา', 'house_number': 1, 'house_type': 'กาลปักษ์'},
    'มาตา': {'thai_meaning': 'แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว', 'house_number': 2, 'house_type': 'เกณฑ์ชะตา'},
    'ลาภะ': {'thai_meaning': 'ลาภยศ โชคลาภ', 'house_number': 3, 'house_type': 'จร'},
    'สหัชชะ': {'thai_meaning': 'เพื่อนฝูง การติดต่อ', 'house_number': 4, 'house_type': 'กาลปักษ์'},
    'สุภะ': {'thai_meaning': 'ความเจริญรุ่งเรือง', 'house_number': 5, 'house_type': 'เกณฑ์ชะตา'},
    'หินะ': {'thai_meaning': 'ความผิดหวัง', 'house_number': 6, 'house_type': 'กาลปักษ์'},
    'อริ': {'thai_meaning': 'ปัญหา อุปสรรค', 'house_number': 7, 'house_type': 'กาลปักษ์'},
    'อัตตะ': {'thai_meaning': 'ตัวท่านเอง', 'house_number': 8, 'house_type': 'กาลปักษ์'},
    'โภคา': {'thai_meaning': 'สินทรัพย์', 'house_number': 9, 'house_type': 'จร'},
}

# Topic mappings for AI topic detection
TOPIC_MAPPINGS = {
    'การเงิน': {
        'keywords': ['เงิน', 'ทรัพย์', 'รายได้', 'ธุรกิจ', 'การเงิน', 'เศรษฐกิจ', 'ค้าขาย', 'ลงทุน', 'หุ้น', 'กำไร', 'ขาดทุน'],
        'subtopics': {
            'การลงทุน': ['หุ้น', 'กองทุน', 'คริปโต', 'อสังหา', 'ทอง', 'พันธบัตร'],
            'ธุรกิจ': ['ค้าขาย', 'ร้านค้า', 'ธุรกิจส่วนตัว', 'สตาร์ทอัพ', 'แฟรนไชส์'],
            'การออม': ['เก็บเงิน', 'ฝากเงิน', 'ออมทรัพย์', 'วางแผนการเงิน']
        }
    },
    'ความรัก': {
        'keywords': ['รัก', 'แฟน', 'คู่ครอง', 'สามี', 'ภรรยา', 'แต่งงาน', 'หมั้น', 'จีบ', 'ความสัมพันธ์', 'คนรัก'],
        'subtopics': {
            'ความสัมพันธ์': ['คบหา', 'เดท', 'จีบ', 'ผูกพัน'],
            'ชีวิตคู่': ['แต่งงาน', 'หมั้น', 'สามี', 'ภรรยา'],
            'อกหัก': ['เลิก', 'นอกใจ', 'เหงา', 'เสียใจ']
        }
    },
    'สุขภาพ': {
        'keywords': ['สุขภาพ', 'ป่วย', 'โรค', 'หมอ', 'รักษา', 'ผ่าตัด', 'ยา', 'แข็งแรง', 'ร่างกาย', 'จิตใจ'],
        'subtopics': {
            'สุขภาพกาย': ['ออกกำลังกาย', 'อาหาร', 'พักผ่อน', 'น้ำหนัก'],
            'สุขภาพจิต': ['เครียด', 'ซึมเศร้า', 'วิตกกังวล', 'นอนไม่หลับ'],
            'การรักษา': ['หมอ', 'โรงพยาบาล', 'ยา', 'การผ่าตัด']
        }
    },
    'การงาน': {
        'keywords': ['งาน', 'อาชีพ', 'เลื่อนตำแหน่ง', 'เงินเดือน', 'หัวหน้า', 'ลูกน้อง', 'บริษัท', 'องค์กร', 'สมัครงาน'],
        'subtopics': {
            'การเติบโต': ['เลื่อนตำแหน่ง', 'เพิ่มเงินเดือน', 'พัฒนาตัวเอง'],
            'การหางาน': ['สมัครงาน', 'สัมภาษณ์', 'ประวัติ', 'เปลี่ยนงาน'],
            'ความสัมพันธ์ในที่ทำงาน': ['หัวหน้า', 'เพื่อนร่วมงาน', 'ลูกน้อง']
        }
    },
    'การศึกษา': {
        'keywords': ['เรียน', 'สอบ', 'โรงเรียน', 'มหาวิทยาลัย', 'วิชา', 'การศึกษา', 'ปริญญา', 'จบ', 'วิทยาลัย'],
        'subtopics': {
            'การเรียน': ['วิชา', 'การบ้าน', 'สอบ', 'คะแนน'],
            'สถานศึกษา': ['โรงเรียน', 'มหาวิทยาลัย', 'วิทยาลัย'],
            'อนาคตการศึกษา': ['เรียนต่อ', 'ทุน', 'ต่างประเทศ']
        }
    }
}

# Mapping of which base corresponds to which house positions
BASE_TO_HOUSE_MAPPING = {
    1: (1, 3),    # Base 1 corresponds to houses 1-3
    2: (4, 6),    # Base 2 corresponds to houses 4-6
    3: (7, 9),    # Base 3 corresponds to houses 7-9
    4: (10, 12)   # Base 4 corresponds to houses 10-12
} 