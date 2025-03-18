import asyncio
import sys
import os
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from ongphra_chat.app.config.database import DatabaseManager
from ongphra_chat.app.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("test_db_connection")

async def test_database_connection():
    """Test the database connection"""
    logger.info("Starting database connection test")
    
    # Get settings
    settings = get_settings()
    logger.info(f"Database settings: host={settings.db_host}, port={settings.db_port}, db={settings.db_name}")
    
    try:
        # Initialize the database connection pool
        await DatabaseManager.initialize_pool()
        logger.info("Database connection pool initialized successfully")
        
        # Test a simple query
        query = "SELECT 1 as test"
        result = await DatabaseManager.fetch_one(query)
        logger.info(f"Test query result: {result}")
        
        # Test a query to get categories
        query = "SELECT * FROM categories LIMIT 5"
        results = await DatabaseManager.fetch(query)
        logger.info(f"Found {len(results)} categories")
        
        for i, category in enumerate(results):
            logger.info(f"Category {i+1}: {category.get('name')} - {category.get('thai_meaning')}")
        
        # Close the database connection pool
        await DatabaseManager.close_pool()
        logger.info("Database connection pool closed")
        
    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}", exc_info=True)
    
    logger.info("Database connection test completed")

if __name__ == "__main__":
    asyncio.run(test_database_connection()) 