# app/repository/db_repository.py
from typing import List, Dict, Any, Optional, TypeVar, Generic, Type
from pydantic import BaseModel
from ongphra_chat.app.repository.base import BaseRepository
from ongphra_chat.app.config.database import DatabaseManager
from ongphra_chat.app.core.logging import get_logger
from app.core.exceptions import RepositoryError
import logging

T = TypeVar('T', bound=BaseModel)

class DBRepository(BaseRepository[T]):
    """Base repository implementation using a database"""
    
    def __init__(
        self,
        model_class: Type[T],
        table_name: str
    ):
        """
        Initialize the repository
        
        Args:
            model_class: Pydantic model class for the entity
            table_name: Database table name
        """
        self.model_class = model_class
        self.table_name = table_name
        
        # Get logger with error handling for file operations
        try:
            self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
            self.logger.info(f"Initialized DB repository for {model_class.__name__} with table: {table_name}")
        except Exception as e:
            # Fallback to basic console logging if file logging fails
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            self.logger.warning(f"Failed to initialize file logger: {str(e)}. Using console logger instead.")
            self.logger.info(f"Initialized DB repository for {model_class.__name__} with table: {table_name}")
    
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID"""
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        self.logger.debug(f"Getting entity by ID: {id}")
        
        try:
            result = await DatabaseManager.fetch_one(query, id)
            if result:
                return self.model_class(**result)
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving entity with ID {id}: {str(e)}", exc_info=True)
            raise RepositoryError(f"Error retrieving entity with ID {id}: {str(e)}")
    
    async def get_all(self) -> List[T]:
        """Get all entities"""
        query = f"SELECT * FROM {self.table_name}"
        self.logger.debug(f"Getting all entities from {self.table_name}")
        
        try:
            results = await DatabaseManager.fetch(query)
            return [self.model_class(**dict(row)) for row in results]
        except Exception as e:
            self.logger.error(f"Error retrieving all entities: {str(e)}", exc_info=True)
            raise RepositoryError(f"Error retrieving all entities: {str(e)}")
    
    async def filter(self, **kwargs) -> List[T]:
        """Filter entities by criteria"""
        conditions = []
        values = []
        
        for i, (key, value) in enumerate(kwargs.items(), start=1):
            conditions.append(f"{key} = %s")
            values.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
        
        self.logger.debug(f"Filtering entities with criteria: {kwargs}")
        
        try:
            results = await DatabaseManager.fetch(query, *values)
            return [self.model_class(**dict(row)) for row in results]
        except Exception as e:
            self.logger.error(f"Error filtering entities with criteria {kwargs}: {str(e)}", exc_info=True)
            raise RepositoryError(f"Error filtering entities: {str(e)}")
    
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        # Convert entity to dict and exclude id if None
        data = entity.model_dump()
        if 'id' in data and data['id'] is None:
            del data['id']
        
        columns = list(data.keys())
        values = list(data.values())
        
        placeholders = ["%s" for _ in range(len(values))]
        
        columns_str = ", ".join(columns)
        placeholders_str = ", ".join(placeholders)
        
        query = f"""
            INSERT INTO {self.table_name} ({columns_str})
            VALUES ({placeholders_str})
        """
        
        self.logger.info(f"Creating new entity in {self.table_name}")
        
        try:
            await DatabaseManager.execute(query, *values)
            # Get the last inserted ID
            last_id_query = "SELECT LAST_INSERT_ID() as id"
            result = await DatabaseManager.fetch_one(last_id_query)
            last_id = result['id']
            
            # Fetch the newly created entity
            return await self.get_by_id(last_id)
        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}", exc_info=True)
            raise RepositoryError(f"Error creating entity: {str(e)}")
    
    async def update(self, id: Any, entity: T) -> T:
        """Update an existing entity"""
        # Convert entity to dict and exclude id
        data = entity.model_dump()
        if 'id' in data:
            del data['id']
        
        columns = list(data.keys())
        values = list(data.values())
        
        set_clause = ", ".join([f"{col} = %s" for col in columns])
        
        query = f"""
            UPDATE {self.table_name}
            SET {set_clause}
            WHERE id = %s
        """
        
        self.logger.info(f"Updating entity with ID {id} in {self.table_name}")
        
        try:
            # Add id to the values list for the WHERE clause
            values.append(id)
            await DatabaseManager.execute(query, *values)
            
            # Fetch the updated entity
            updated_entity = await self.get_by_id(id)
            if not updated_entity:
                raise RepositoryError(f"Entity with ID {id} not found")
            return updated_entity
        except Exception as e:
            self.logger.error(f"Error updating entity with ID {id}: {str(e)}", exc_info=True)
            raise RepositoryError(f"Error updating entity: {str(e)}")
    
    async def delete(self, id: Any) -> bool:
        """Delete entity by ID"""
        query = f"DELETE FROM {self.table_name} WHERE id = %s"
        
        self.logger.info(f"Deleting entity with ID {id} from {self.table_name}")
        
        try:
            result = await DatabaseManager.execute(query, id)
            return result > 0
        except Exception as e:
            self.logger.error(f"Error deleting entity with ID {id}: {str(e)}", exc_info=True)
            raise RepositoryError(f"Error deleting entity: {str(e)}")
    
    async def execute_raw_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results"""
        self.logger.debug(f"Executing raw query: {query}")
        
        try:
            results = await DatabaseManager.fetch(query, *args)
            return results
        except Exception as e:
            self.logger.error(f"Error executing raw query: {str(e)}", exc_info=True)
            raise RepositoryError(f"Error executing query: {str(e)}")