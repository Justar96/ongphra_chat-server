# app/tests/test_repositories.py
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.repository.reading_repository import ReadingRepository, get_reading_repository
from app.repository.category_repository import CategoryRepository, get_category_repository
from app.services.reading_service import ReadingService, get_reading_service
from app.core.logging import setup_logging, get_logger
from app.domain.meaning import Reading, Category

# Setup logging
setup_logging()
logger = get_logger("test_repositories")

async def test_repositories():
    """Test direct repository instantiation"""
    logger.info("Testing direct repository instantiation...")
    
    # Create repositories directly
    reading_repo = ReadingRepository(Reading)
    category_repo = CategoryRepository(Category)
    
    # Try to create a service directly
    service = ReadingService(reading_repo, category_repo)
    
    logger.info(f"Successfully created repositories and service directly")
    return True

async def test_repository_factory_functions():
    """Test repository factory functions"""
    logger.info("Testing repository factory functions...")
    
    # Use factory functions
    reading_repo = get_reading_repository()
    category_repo = get_category_repository()
    
    logger.info(f"Successfully created repositories using factory functions")
    return True

async def test_service_factory_function():
    """Test service factory function"""
    logger.info("Testing service factory function...")
    
    # Use service factory function
    service = await get_reading_service()
    
    logger.info(f"Successfully created service using factory function")
    return True

async def main():
    """Run all tests"""
    logger.info("Starting repository tests...")
    
    try:
        # Test direct repository instantiation
        await test_repositories()
        
        # Test repository factory functions
        await test_repository_factory_functions()
        
        # Test service factory function
        await test_service_factory_function()
        
        logger.info("All repository tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        
    logger.info("Repository tests completed.")

if __name__ == "__main__":
    asyncio.run(main()) 