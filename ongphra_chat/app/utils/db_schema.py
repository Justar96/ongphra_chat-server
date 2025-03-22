from sqlalchemy import Column, Integer, String, Text, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class FortuneCategory(Base):
    """Database model for fortune categories."""
    __tablename__ = 'fortune_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    thai_name = Column(String(50), nullable=False)
    meaning = Column(Text, nullable=False)
    house_type = Column(String(50), nullable=True)
    base_number = Column(Integer, nullable=False)  # 1, 2, or 3
    
    def __repr__(self):
        return f"<FortuneCategory(name='{self.name}', thai_name='{self.thai_name}')>"

class FortunePairInterpretation(Base):
    """Database model for interpretations of pairs of fortune categories."""
    __tablename__ = 'fortune_pair_interpretations'
    
    id = Column(Integer, primary_key=True)
    
    # Categories
    category_a_id = Column(Integer, ForeignKey('fortune_categories.id'), nullable=False)
    category_b_id = Column(Integer, ForeignKey('fortune_categories.id'), nullable=False)
    
    # Values
    value_a = Column(Integer, nullable=False)
    value_b = Column(Integer, nullable=False)
    
    # Interpretation
    heading = Column(String(100), nullable=False)
    meaning = Column(Text, nullable=False)
    influence = Column(String(50), nullable=True)
    
    # Relationships
    category_a = relationship("FortuneCategory", foreign_keys=[category_a_id])
    category_b = relationship("FortuneCategory", foreign_keys=[category_b_id])
    
    def __repr__(self):
        return f"<FortunePairInterpretation(category_a='{self.category_a.name}', category_b='{self.category_b.name}', value_a={self.value_a}, value_b={self.value_b})>"

def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)

def get_engine(connection_string):
    """Get a SQLAlchemy engine."""
    return create_engine(connection_string)

def get_session(engine):
    """Get a SQLAlchemy session."""
    Session = sessionmaker(bind=engine)
    return Session()

def seed_categories(session):
    """Seed the database with fortune categories."""
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

def seed_pair_interpretations(session):
    """Seed the database with some example pair interpretations."""
    # This is just a starter example - you would populate with real interpretations
    
    # Get some categories
    attana = session.query(FortuneCategory).filter_by(thai_name="อัตตะ").first()
    tanu = session.query(FortuneCategory).filter_by(thai_name="ตะนุ").first()
    
    # Create an interpretation for a high value pair
    if attana and tanu:
        interpretation = FortunePairInterpretation(
            category_a_id=attana.id,
            category_b_id=tanu.id,
            value_a=7,
            value_b=7,
            heading="ตัวตนและบุคลิกภาพที่เข้มแข็ง",
            meaning="คุณมีความเป็นตัวของตัวเองสูงมาก ทั้งในแง่ของความคิดและการแสดงออก มีความมั่นใจในตัวเองสูง สามารถตัดสินใจได้ดีด้วยตัวเอง แต่ในบางครั้งอาจดูเป็นคนที่ยึดมั่นในความคิดตัวเองมากเกินไป ควรรับฟังความคิดเห็นของผู้อื่นบ้าง",
            influence="ดี"
        )
        session.add(interpretation)
        
    # Create more interpretations here...
    
    # Commit the session
    session.commit()

if __name__ == "__main__":
    # Example usage
    connection_string = "sqlite:///fortune.db"
    engine = get_engine(connection_string)
    create_tables(engine)
    
    session = get_session(engine)
    seed_categories(session)
    seed_pair_interpretations(session)
    session.close() 