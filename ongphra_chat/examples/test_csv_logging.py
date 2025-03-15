# examples/test_csv_logging.py
import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the logging utility
from app.core.logging import get_logger

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(LOGS_DIR, "test_csv.log")
csv_log_file = os.path.join(LOGS_DIR, "csv_operations.log")

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'  # Ensure UTF-8 encoding for Thai characters
        )
    ]
)

# Configure CSV operations logger
csv_logger = logging.getLogger('app.repository')
csv_logger.setLevel(logging.DEBUG)
csv_handler = RotatingFileHandler(
    csv_log_file,
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3,
    encoding='utf-8'  # Ensure UTF-8 encoding for Thai characters
)
csv_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
csv_logger.addHandler(csv_handler)

# Get test logger
logger = get_logger("test_csv_logging")
logger.info(f"Logging to {log_file} and {csv_log_file}")

# Mock data paths for testing
DATA_DIR = BASE_DIR / "data"
CATEGORIES_PATH = DATA_DIR / "categories.csv"
READINGS_PATH = DATA_DIR / "readings.csv"

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Create mock CSV files for testing if they don't exist
if not os.path.exists(CATEGORIES_PATH):
    logger.info(f"Creating mock categories file at {CATEGORIES_PATH}")
    with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
        f.write("id,category_name,category_thai_name,description\n")
        f.write("1,GENERAL,GENERAL,General readings\n")
        f.write("2,CAREER,CAREER,Career readings\n")
        f.write("3,RELATIONSHIP,RELATIONSHIP,Relationship readings\n")
        f.write("4,FINANCE,FINANCE,Finance readings\n")
        f.write("5,HEALTH,HEALTH,Health readings\n")

if not os.path.exists(READINGS_PATH):
    logger.info(f"Creating mock readings file at {READINGS_PATH}")
    with open(READINGS_PATH, 'w', encoding='utf-8') as f:
        f.write("id,base,position,relationship_id,content,thai_content,heading,meaning,category\n")
        f.write("1,1,1,2,Career reading,Career reading,Career Path,Your career path is promising,CAREER\n")
        f.write("2,1,2,3,Love reading,Love reading,Love Life,Your love life is stable,RELATIONSHIP\n")
        f.write("3,2,1,4,Finance reading,Finance reading,Financial Status,Your finances are improving,FINANCE\n")
        f.write("4,3,1,5,Health reading,Health reading,Health Status,Your health is good,HEALTH\n")
        f.write("5,4,1,1,General reading,General reading,General Outlook,Your future looks bright,GENERAL\n")

# Now import the rest of the modules
from app.domain.meaning import Category, Reading
from app.repository.category_repository import CategoryRepository
from app.repository.reading_repository import ReadingRepository
from app.services.meaning import MeaningService
from app.domain.bases import Bases

async def test_csv_repositories():
    """Test CSV repository operations with logging"""
    logger.info("Starting CSV repository test")
    
    # Initialize repositories with mock paths
    category_repo = CategoryRepository(str(CATEGORIES_PATH), Category)
    reading_repo = ReadingRepository(str(READINGS_PATH), Reading)
    
    # Test category operations
    logger.info("Testing category operations")
    all_categories = await category_repo.get_all()
    logger.info(f"Found {len(all_categories)} categories")
    
    # Test getting a category by name
    career_category = await category_repo.get_by_name("CAREER")
    if career_category:
        logger.info(f"Found CAREER category: {career_category.id} - {career_category.category_name}")
    else:
        logger.warning("CAREER category not found")
    
    # Test reading operations
    logger.info("Testing reading operations")
    
    # Get readings for a specific base and position
    base1_pos1_readings = await reading_repo.get_by_base_and_position(1, 1)
    logger.info(f"Found {len(base1_pos1_readings)} readings for base 1, position 1")
    
    # Get readings by category
    if career_category:
        career_readings = await reading_repo.get_by_categories([career_category.id])
        logger.info(f"Found {len(career_readings)} readings for CAREER category")
    
    logger.info("CSV repository test completed")
    return all_categories

async def test_meaning_service():
    """Test meaning service with logging"""
    logger.info("Starting meaning service test")
    
    # Initialize repositories with mock paths
    category_repo = CategoryRepository(str(CATEGORIES_PATH), Category)
    reading_repo = ReadingRepository(str(READINGS_PATH), Reading)
    
    # Initialize meaning service
    meaning_service = MeaningService(category_repo, reading_repo)
    
    # Create a test bases object
    test_bases = Bases(
        base1=[1, 2, 3, 4, 5, 6, 7],
        base2=[7, 6, 5, 4, 3, 2, 1],
        base3=[4, 5, 6, 7, 1, 2, 3],
        base4=[3, 2, 1, 7, 6, 5, 4]
    )
    
    # Test with different questions
    test_questions = [
        "Career in the future",  # Career
        "Love life",  # Love
        "Health status",  # Health
        "Financial improvement",  # Finance
        "Life guidance"  # General
    ]
    
    for question in test_questions:
        logger.info(f"Testing question: '{question}'")
        meanings = await meaning_service.extract_meanings(test_bases, question)
        logger.info(f"Extracted {len(meanings.items)} meanings for question")
        
        # Log the first few meanings
        for i, meaning in enumerate(meanings.items[:3], 1):
            logger.info(f"Meaning {i}: Base {meaning.base}, Position {meaning.position}, Value {meaning.value}")
            logger.info(f"  Heading: {meaning.heading}")
            logger.info(f"  Category: {meaning.category}")
    
    logger.info("Meaning service test completed")

async def main():
    """Main function to run the tests"""
    logger.info("Starting CSV logging test")
    
    try:
        # Test CSV repositories
        await test_csv_repositories()
        
        # Test meaning service
        await test_meaning_service()
        
        logger.info("All tests completed successfully")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
    
    logger.info("CSV logging test completed")

if __name__ == "__main__":
    asyncio.run(main()) 