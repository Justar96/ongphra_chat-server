# app/config/database.py
import aiomysql
import logging
from typing import Dict, List, Any, Optional
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager for MariaDB/MySQL using aiomysql"""
    
    _pool = None
    
    @classmethod
    async def initialize_pool(cls):
        """Initialize the connection pool"""
        if cls._pool is None:
            try:
                logger.info("Initializing database connection pool")
                cls._pool = await aiomysql.create_pool(
                    host=settings.db_host,
                    port=settings.db_port,
                    user=settings.db_user,
                    password=settings.db_password,
                    db=settings.db_name,
                    minsize=settings.db_pool_min_size,
                    maxsize=settings.db_pool_max_size,
                    autocommit=True
                )
                logger.info("Database connection pool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize database connection pool: {str(e)}", exc_info=True)
                raise
    
    @classmethod
    async def close_pool(cls):
        """Close the connection pool"""
        if cls._pool:
            logger.info("Closing database connection pool")
            cls._pool.close()
            await cls._pool.wait_closed()
            cls._pool = None
            logger.info("Database connection closed")
    
    @classmethod
    async def fetch(cls, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a query and return all results"""
        if cls._pool is None:
            await cls.initialize_pool()
        
        async with cls._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    await cursor.execute(query, args if args else None)
                    results = await cursor.fetchall()
                    return results
                except Exception as e:
                    logger.error(f"Database query error: {str(e)}\nQuery: {query}\nArgs: {args}", exc_info=True)
                    raise
    
    @classmethod
    async def fetch_one(cls, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute a query and return the first result"""
        if cls._pool is None:
            await cls.initialize_pool()
        
        async with cls._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    await cursor.execute(query, args if args else None)
                    result = await cursor.fetchone()
                    return result
                except Exception as e:
                    logger.error(f"Database query error: {str(e)}\nQuery: {query}\nArgs: {args}", exc_info=True)
                    raise
    
    @classmethod
    async def execute(cls, query: str, *args) -> int:
        """Execute a query and return the affected rows"""
        if cls._pool is None:
            await cls.initialize_pool()
        
        async with cls._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, args if args else None)
                    return cursor.rowcount
                except Exception as e:
                    logger.error(f"Database query error: {str(e)}\nQuery: {query}\nArgs: {args}", exc_info=True)
                    raise
    
    @classmethod
    async def execute_many(cls, query: str, args_list) -> int:
        """Execute a query with multiple sets of parameters"""
        if cls._pool is None:
            await cls.initialize_pool()
        
        async with cls._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.executemany(query, args_list)
                    return cursor.rowcount
                except Exception as e:
                    logger.error(f"Database query error: {str(e)}\nQuery: {query}", exc_info=True)
                    raise
    
    @classmethod
    async def execute_raw_query(cls, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results"""
        return await cls.fetch(query, *args)