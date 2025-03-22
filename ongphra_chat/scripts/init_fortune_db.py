import os
import sys
import logging
from pathlib import Path

# Add the parent directory to sys.path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Import the required modules
from app.utils.db_schema import (
    Base, 
    FortuneCategory, 
    FortunePairInterpretation, 
    create_tables, 
    get_engine, 
    get_session
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database(db_path):
    """Initialize the database with schema and seed data."""
    try:
        # Create the database directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        # Create the database connection string
        connection_string = f"sqlite:///{db_path}"
        logger.info(f"Initializing database at {db_path}")
        
        # Create the engine and tables
        engine = get_engine(connection_string)
        create_tables(engine)
        
        # Create a session
        session = get_session(engine)
        
        # Seed the database with categories
        seed_categories(session)
        
        # Seed the database with pair interpretations
        seed_pair_interpretations(session)
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def seed_categories(session):
    """Seed the database with fortune categories."""
    logger.info("Seeding categories...")
    
    # Check if categories already exist
    existing_count = session.query(FortuneCategory).count()
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing categories, skipping seed")
        return
    
    # Base 1 categories
    base1_categories = [
        {"name": "attana", "thai_name": "อัตตะ", "meaning": "ตัวท่านเอง", "house_type": "กาลปักษ์", "base_number": 1},
        {"name": "hina", "thai_name": "หินะ", "meaning": "ความผิดหวัง", "house_type": "กาลปักษ์", "base_number": 1},
        {"name": "thana", "thai_name": "ธานัง", "meaning": "เรื่องเงิน ๆ ทอง ๆ", "house_type": "จร", "base_number": 1},
        {"name": "pita", "thai_name": "ปิตา", "meaning": "พ่อหรือผู้ใหญ่ เรื่องนอกบ้าน", "house_type": "เกณฑ์ชะตา", "base_number": 1},
        {"name": "mata", "thai_name": "มาตา", "meaning": "แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว", "house_type": "เกณฑ์ชะตา", "base_number": 1},
        {"name": "bhoga", "thai_name": "โภคา", "meaning": "สินทรัพย์", "house_type": "จร", "base_number": 1},
        {"name": "majjhima", "thai_name": "มัชฌิมา", "meaning": "เรื่องกลาง ๆ ไม่หนักหนา", "house_type": "กาลปักษ์", "base_number": 1},
    ]
    
    # Base 2 categories
    base2_categories = [
        {"name": "tanu", "thai_name": "ตะนุ", "meaning": "ตัวท่านเอง", "house_type": "จร", "base_number": 2},
        {"name": "kadumpha", "thai_name": "กดุมภะ", "meaning": "รายได้รายจ่าย", "house_type": "กาลปักษ์", "base_number": 2},
        {"name": "sahajja", "thai_name": "สหัชชะ", "meaning": "เพื่อนฝูง การติดต่อ", "house_type": "กาลปักษ์", "base_number": 2},
        {"name": "phantu", "thai_name": "พันธุ", "meaning": "ญาติพี่น้อง", "house_type": "เกณฑ์ชะตา", "base_number": 2},
        {"name": "putta", "thai_name": "ปุตตะ", "meaning": "เรื่องลูก การเริ่มต้น", "house_type": "จร", "base_number": 2},
        {"name": "ari", "thai_name": "อริ", "meaning": "ปัญหา อุปสรรค", "house_type": "กาลปักษ์", "base_number": 2},
        {"name": "patni", "thai_name": "ปัตนิ", "meaning": "คู่ครอง", "house_type": "กาลปักษ์", "base_number": 2},
    ]
    
    # Base 3 categories
    base3_categories = [
        {"name": "marana", "thai_name": "มรณะ", "meaning": "เรื่องเจ็บป่วย", "house_type": "กาลปักษ์", "base_number": 3},
        {"name": "subha", "thai_name": "สุภะ", "meaning": "ความเจริญรุ่งเรือง", "house_type": "เกณฑ์ชะตา", "base_number": 3},
        {"name": "kamma", "thai_name": "กัมมะ", "meaning": "หน้าที่การงาน", "house_type": "เกณฑ์ชะตา", "base_number": 3},
        {"name": "labha", "thai_name": "ลาภะ", "meaning": "ลาภยศ โชคลาภ", "house_type": "จร", "base_number": 3},
        {"name": "phayaya", "thai_name": "พยายะ", "meaning": "สิ่งไม่ดี เรื่องปิดบัง ซ่อนเร้น", "house_type": "กาลปักษ์", "base_number": 3},
        {"name": "thasa", "thai_name": "ทาสา", "meaning": "เหน็จเหนื่อยเพื่อคนอื่น ส่วนรวม", "house_type": "กาลปักษ์", "base_number": 3},
        {"name": "thasi", "thai_name": "ทาสี", "meaning": "การเหน็จเหนื่อยเพื่อตัวเอง", "house_type": "เกณฑ์ชะตา", "base_number": 3},
    ]
    
    # Add all categories to the session
    for category_data in base1_categories + base2_categories + base3_categories:
        category = FortuneCategory(**category_data)
        session.add(category)
    
    # Commit the session
    session.commit()
    logger.info(f"Added {len(base1_categories + base2_categories + base3_categories)} categories")

def seed_pair_interpretations(session):
    """Seed the database with sample pair interpretations."""
    logger.info("Seeding pair interpretations...")
    
    # Check if interpretations already exist
    existing_count = session.query(FortunePairInterpretation).count()
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing interpretations, skipping seed")
        return
    
    # Sample interpretations - in a real system, you'd have many more
    interpretations = []
    
    # Get category IDs
    category_map = {}
    for category in session.query(FortuneCategory).all():
        category_map[category.name] = category.id
    
    # Add some money-related interpretations
    if 'thana' in category_map and 'kadumpha' in category_map:
        interpretations.extend([
            {
                "category_a_id": category_map['thana'],
                "category_b_id": category_map['kadumpha'],
                "value_a": 7,
                "value_b": 7,
                "heading": "การเงินและรายได้ที่มั่นคง",
                "meaning": "คุณมีโอกาสที่ดีในการสร้างความมั่งคั่งทางการเงิน มีความสามารถในการจัดการรายรับรายจ่ายได้อย่างมีประสิทธิภาพ และมีโอกาสในการลงทุนที่ให้ผลตอบแทนสูง ควรใช้ความสามารถนี้ในการวางแผนการเงินระยะยาว",
                "influence": "ดีมาก"
            },
            {
                "category_a_id": category_map['thana'],
                "category_b_id": category_map['kadumpha'],
                "value_a": 2,
                "value_b": 2,
                "heading": "ความท้าทายด้านการเงิน",
                "meaning": "คุณอาจพบกับความท้าทายในการจัดการด้านการเงิน ควรระมัดระวังในการใช้จ่ายและการลงทุน ควรศึกษาเพิ่มเติมเกี่ยวกับการวางแผนทางการเงินและการจัดการรายได้ การขอคำปรึกษาจากผู้เชี่ยวชาญอาจช่วยได้",
                "influence": "ต้องระวัง"
            },
            {
                "category_a_id": category_map['thana'],
                "category_b_id": category_map['kadumpha'],
                "value_a": 7,
                "value_b": 3,
                "heading": "โอกาสทางการเงินที่ต้องบริหารให้ดี",
                "meaning": "คุณมีโอกาสดีในการหารายได้ แต่อาจมีความท้าทายในการจัดการรายจ่าย ควรเน้นการวางแผนการใช้จ่ายให้มีประสิทธิภาพมากขึ้น เพื่อให้เกิดความสมดุลระหว่างรายรับและรายจ่าย",
                "influence": "ผสมผสาน"
            }
        ])
    
    # Add some career-related interpretations
    if 'kamma' in category_map and 'labha' in category_map:
        interpretations.extend([
            {
                "category_a_id": category_map['kamma'],
                "category_b_id": category_map['labha'],
                "value_a": 6,
                "value_b": 6,
                "heading": "ความสำเร็จในหน้าที่การงาน",
                "meaning": "คุณมีแนวโน้มที่จะประสบความสำเร็จในหน้าที่การงาน มีโอกาสได้รับการยอมรับและการเลื่อนตำแหน่ง โชคลาภมักจะเข้ามาในช่วงเวลาที่เหมาะสม ทำให้งานของคุณราบรื่นและนำมาซึ่งความมั่นคง",
                "influence": "ดี"
            },
            {
                "category_a_id": category_map['kamma'],
                "category_b_id": category_map['labha'],
                "value_a": 3,
                "value_b": 7,
                "heading": "โชคดีที่ช่วยในการทำงาน",
                "meaning": "แม้จะพบความท้าทายในการทำงาน แต่คุณมักมีโชคที่ช่วยให้สถานการณ์พลิกผัน ความสำเร็จของคุณอาจมาจากโอกาสที่ดีที่เข้ามาในเวลาที่เหมาะสม ควรเปิดรับโอกาสใหม่ๆ และพร้อมที่จะปรับตัว",
                "influence": "ดี"
            }
        ])
    
    # Add some self-identity interpretations
    if 'attana' in category_map and 'tanu' in category_map:
        interpretations.extend([
            {
                "category_a_id": category_map['attana'],
                "category_b_id": category_map['tanu'],
                "value_a": 7,
                "value_b": 7,
                "heading": "ตัวตนและบุคลิกภาพที่เข้มแข็ง",
                "meaning": "คุณมีความเป็นตัวของตัวเองสูงมาก ทั้งในแง่ของความคิดและการแสดงออก มีความมั่นใจในตัวเองสูง สามารถตัดสินใจได้ดีด้วยตัวเอง แต่ในบางครั้งอาจดูเป็นคนที่ยึดมั่นในความคิดตัวเองมากเกินไป ควรรับฟังความคิดเห็นของผู้อื่นบ้าง",
                "influence": "ดี"
            }
        ])
    
    # Add some family-related interpretations
    if 'patni' in category_map and 'putta' in category_map:
        interpretations.extend([
            {
                "category_a_id": category_map['patni'],
                "category_b_id": category_map['putta'],
                "value_a": 6,
                "value_b": 6,
                "heading": "ครอบครัวที่อบอุ่นและมั่นคง",
                "meaning": "คุณมีแนวโน้มที่จะมีครอบครัวที่อบอุ่นและมั่นคง ความสัมพันธ์กับคู่ครองและบุตรเต็มไปด้วยความเข้าใจและความรัก คุณให้ความสำคัญกับครอบครัว และสมาชิกในครอบครัวก็ให้ความสำคัญกับคุณเช่นกัน",
                "influence": "ดีมาก"
            }
        ])
    
    # Add interpretations for issues and obstacles (อริ)
    if 'ari' in category_map and 'pita' in category_map:
        interpretations.extend([
            {
                "category_a_id": category_map['ari'],
                "category_b_id": category_map['pita'],
                "value_a": 7,
                "value_b": 7,
                "heading": "ความท้าทายจากอำนาจและผู้ใหญ่",
                "meaning": "คุณมีความโดดเด่นในการเผชิญหน้ากับปัญหาที่เกี่ยวข้องกับผู้มีอำนาจหรือผู้ใหญ่ ความท้าทายเหล่านี้จะช่วยเสริมสร้างความแข็งแกร่งและประสบการณ์ที่มีค่า คุณมีความสามารถในการจัดการกับอุปสรรคเหล่านี้ด้วยวิธีที่ฉลาดและมีประสิทธิภาพ",
                "influence": "ผสมผสาน"
            }
        ])
    
    # Add interpretations for health issues (มรณะ)
    if 'marana' in category_map and 'subha' in category_map:
        interpretations.extend([
            {
                "category_a_id": category_map['marana'],
                "category_b_id": category_map['subha'],
                "value_a": 6,
                "value_b": 1,
                "heading": "การจัดการด้านสุขภาพ",
                "meaning": "คุณอาจพบปัญหาสุขภาพที่ต้องให้ความใส่ใจ แต่ด้วยการดูแลตัวเองที่ดีและการระมัดระวัง ปัญหาเหล่านี้จะไม่ส่งผลกระทบรุนแรงต่อชีวิตของคุณ ควรใส่ใจในเรื่องการพักผ่อนและการออกกำลังกายให้เพียงพอ",
                "influence": "ต้องระวัง"
            }
        ])
    
    # Add interpretations for wealth and obstacles
    if 'thana' in category_map and 'ari' in category_map:
        interpretations.extend([
            {
                "category_a_id": category_map['thana'],
                "category_b_id": category_map['ari'],
                "value_a": 6,
                "value_b": 7,
                "heading": "อุปสรรคในการสร้างความมั่งคั่ง",
                "meaning": "แม้จะมีศักยภาพทางการเงินที่ดี แต่คุณอาจพบกับอุปสรรคในการสร้างความมั่งคั่ง อุปสรรคเหล่านี้จะเป็นบททดสอบและช่วยให้คุณเรียนรู้วิธีจัดการกับปัญหาอย่างชาญฉลาด การอดทนและมีวินัยจะเป็นกุญแจสำคัญในการก้าวข้ามความท้าทายเหล่านี้",
                "influence": "ผสมผสาน"
            }
        ])
    
    # Add more interpretations for parent-child relationships
    if 'pita' in category_map and 'putta' in category_map:
        interpretations.extend([
            {
                "category_a_id": category_map['pita'],
                "category_b_id": category_map['putta'],
                "value_a": 7,
                "value_b": 6,
                "heading": "ความสัมพันธ์ระหว่างพ่อและลูก",
                "meaning": "คุณมีความสัมพันธ์ที่แข็งแกร่งกับพ่อหรือบุตร ความสัมพันธ์นี้เป็นแหล่งพลังและแรงบันดาลใจในชีวิตของคุณ คุณได้รับการสนับสนุนที่ดีจากครอบครัวและความสัมพันธ์นี้ช่วยเสริมสร้างความแข็งแกร่งให้กับคุณในทุกด้านของชีวิต",
                "influence": "ดี"
            }
        ])
    
    # Add interpretations to the session
    for interp_data in interpretations:
        interp = FortunePairInterpretation(**interp_data)
        session.add(interp)
    
    # Commit the session
    session.commit()
    logger.info(f"Added {len(interpretations)} pair interpretations")

if __name__ == "__main__":
    # Get the database path from command line args or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else "instance/fortune.db"
    
    # Initialize the database
    init_database(db_path) 