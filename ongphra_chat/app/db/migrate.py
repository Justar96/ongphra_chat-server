# app/db/migrate.py
import asyncio
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports to work correctly
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from app.config.database import DatabaseManager
from app.core.logging import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

async def run_migration():
    """Run all SQL migration files sequentially"""
    try:
        logger.info("Starting database migration")
        
        # Initialize database connection
        await DatabaseManager.initialize_pool()
        logger.info("Database connection established")
        
        # Get migration files directory path
        migrations_dir = Path(__file__).parent / "migrations"
        
        # List all SQL files in the migrations directory
        sql_files = sorted([f for f in migrations_dir.glob("*.sql")])
        
        if not sql_files:
            logger.warning("No migration files found")
            return
        
        logger.info(f"Found {len(sql_files)} migration files to process")
        
        # Execute each migration file
        for sql_file in sql_files:
            logger.info(f"Processing migration: {sql_file.name}")
            
            # Read SQL content
            with open(sql_file, "r") as f:
                sql_content = f.read()
            
            # Execute SQL statements
            try:
                # Get a connection from the pool
                conn = await DatabaseManager.get_connection()
                async with conn as connection:
                    async with connection.cursor() as cursor:
                        await cursor.execute(sql_content)
                        logger.info(f"Migration {sql_file.name} executed successfully")
            except Exception as e:
                logger.error(f"Error executing migration {sql_file.name}: {str(e)}", exc_info=True)
                raise
        
        logger.info("Database migration completed successfully")
    
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Close database connection
        await DatabaseManager.close_pool()
        logger.info("Database connection closed")

if __name__ == "__main__":
    try:
        asyncio.run(run_migration())
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
    sys.exit(0) 