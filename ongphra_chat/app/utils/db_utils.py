import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.config.database import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default database connection string
DEFAULT_DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING", "sqlite:///instance/fortune.db")

def get_engine(connection_string=None):
    """
    Get a SQLAlchemy engine.
    
    Args:
        connection_string: Database connection string. If None, uses the default.
        
    Returns:
        SQLAlchemy engine
    """
    connection_string = connection_string or DEFAULT_DB_CONNECTION_STRING
    return create_engine(connection_string)

def get_session_maker(engine=None):
    """
    Get a SQLAlchemy session maker.
    
    Args:
        engine: SQLAlchemy engine. If None, creates a new engine with the default connection string.
        
    Returns:
        SQLAlchemy session maker
    """
    engine = engine or get_engine()
    return sessionmaker(bind=engine)

@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_fortune_pair_interpretation(category_a: str, category_b: str, value_a: int, value_b: int, session: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """
    Get the interpretation for a pair of categories from the database.
    
    Args:
        category_a: The name of the first category
        category_b: The name of the second category
        value_a: The value of the first category
        value_b: The value of the second category
        session: Optional database session
        
    Returns:
        A dictionary with heading, meaning, and influence if found, None otherwise
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
        
    try:
        # Determine influence type based on values
        influence_type = "ดี" if (value_a >= 5 and value_b >= 5) else "กลาง"
        if value_a <= 3 and value_b <= 3:
            influence_type = "ร้าย"
        
        # Query the database for the interpretation
        query = text("""
            SELECT r.heading, r.meaning, r.influence_type
            FROM readings r
            JOIN category_combinations cc ON r.combination_id = cc.id
            JOIN categories c1 ON cc.category1_id = c1.id
            JOIN categories c2 ON cc.category2_id = c2.id
            WHERE ((c1.name = :cat_a AND c2.name = :cat_b)
               OR (c1.name = :cat_b AND c2.name = :cat_a))
               AND r.influence_type = :influence_type
            LIMIT 1
        """)
        
        result = session.execute(query, {
            "cat_a": category_a, 
            "cat_b": category_b,
            "influence_type": influence_type
        }).fetchone()
        
        if result:
            return {
                "heading": result[0],
                "meaning": result[1],
                "influence": result[2]
            }
        
        # If no specific influence type found, try any reading for this combination
        query = text("""
            SELECT r.heading, r.meaning, r.influence_type
            FROM readings r
            JOIN category_combinations cc ON r.combination_id = cc.id
            JOIN categories c1 ON cc.category1_id = c1.id
            JOIN categories c2 ON cc.category2_id = c2.id
            WHERE (c1.name = :cat_a AND c2.name = :cat_b)
               OR (c1.name = :cat_b AND c2.name = :cat_a)
            LIMIT 1
        """)
        
        result = session.execute(query, {"cat_a": category_a, "cat_b": category_b}).fetchone()
        
        if result:
            return {
                "heading": result[0],
                "meaning": result[1],
                "influence": result[2]
            }
        
        return None
    except Exception as e:
        logger.error(f"Error getting interpretation for {category_a} and {category_b}: {e}")
        return None
    finally:
        if close_session:
            session.close()

def get_category_thai_name(category_name: str, session: Optional[Session] = None) -> Optional[str]:
    """
    Get the Thai name for a category from the database.
    
    Args:
        category_name: The English name of the category
        session: Optional database session
        
    Returns:
        The Thai name of the category if found, None otherwise
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
        
    try:
        # Query the database for the category
        query = text("""
            SELECT name, thai_meaning 
            FROM categories 
            WHERE name = :name OR name LIKE :like_name
        """)
        
        result = session.execute(query, {"name": category_name, "like_name": f"%{category_name}%"}).fetchone()
        
        if result:
            return result[1]  # Return thai_meaning
        
        return None
    except Exception as e:
        logger.error(f"Error getting Thai name for category {category_name}: {e}")
        return None
    finally:
        if close_session:
            session.close()

def get_category_pair_heading(category_a: str, category_b: str, session: Optional[Session] = None) -> Optional[str]:
    """
    Get the heading for a pair of categories from the database.
    
    Args:
        category_a: The name of the first category
        category_b: The name of the second category
        session: Optional database session
        
    Returns:
        The heading for the pair if found, None otherwise
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
        
    try:
        # Query the database for the combination
        query = text("""
            SELECT r.heading
            FROM readings r
            JOIN category_combinations cc ON r.combination_id = cc.id
            JOIN categories c1 ON cc.category1_id = c1.id
            JOIN categories c2 ON cc.category2_id = c2.id
            WHERE (c1.name = :cat_a AND c2.name = :cat_b)
               OR (c1.name = :cat_b AND c2.name = :cat_a)
            LIMIT 1
        """)
        
        result = session.execute(query, {"cat_a": category_a, "cat_b": category_b}).fetchone()
        
        if result:
            return result[0]  # Return heading
        
        return None
    except Exception as e:
        logger.error(f"Error getting heading for categories {category_a} and {category_b}: {e}")
        return None
    finally:
        if close_session:
            session.close()

def get_all_categories(session: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Get all fortune categories from the database.
    
    Args:
        session: Optional database session
        
    Returns:
        A list of category dictionaries
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
        
    try:
        # Query all categories
        query = text("""
            SELECT id, name, thai_meaning, house_number, house_type 
            FROM categories 
            ORDER BY house_number, name
        """)
        
        results = session.execute(query).fetchall()
        
        categories = []
        for row in results:
            categories.append({
                "id": row[0],
                "name": row[1],
                "thai_meaning": row[2],
                "house_number": row[3],
                "house_type": row[4]
            })
        
        return categories
    except Exception as e:
        logger.error(f"Error getting all categories: {e}")
        return []
    finally:
        if close_session:
            session.close()

def get_combinations_for_category(category_name: str, session: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Get all combinations involving a specific category.
    
    Args:
        category_name: The name of the category
        session: Optional database session
        
    Returns:
        A list of combination dictionaries
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
        
    try:
        # Query combinations for this category
        query = text("""
            SELECT cc.id, cc.file_name, 
                   c1.name AS category1, c2.name AS category2, 
                   c3.name AS category3
            FROM category_combinations cc
            JOIN categories c1 ON cc.category1_id = c1.id
            JOIN categories c2 ON cc.category2_id = c2.id
            LEFT JOIN categories c3 ON cc.category3_id = c3.id
            WHERE c1.name = :cat_name
               OR c2.name = :cat_name
               OR c3.name = :cat_name
            ORDER BY cc.file_name
        """)
        
        results = session.execute(query, {"cat_name": category_name}).fetchall()
        
        combinations = []
        for row in results:
            combinations.append({
                "id": row[0],
                "file_name": row[1],
                "category1": row[2],
                "category2": row[3],
                "category3": row[4] if row[4] else None
            })
        
        return combinations
    except Exception as e:
        logger.error(f"Error getting combinations for category {category_name}: {e}")
        return []
    finally:
        if close_session:
            session.close() 