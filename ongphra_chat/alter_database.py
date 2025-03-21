import pymysql
from app.config.settings import get_settings

settings = get_settings()

def alter_database():
    """Alter the database tables to add the meta_data column."""
    print("Altering database tables to add meta_data column...")
    
    # Connection object declared in outer scope to ensure it's available in finally block
    conn = None
    
    try:
        # Connect to the database
        conn = pymysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # Check if meta_data column exists in chat_sessions
            cursor.execute("SHOW COLUMNS FROM chat_sessions LIKE 'meta_data'")
            meta_data_exists_sessions = cursor.fetchone()
            
            if not meta_data_exists_sessions:
                print("Adding meta_data column to chat_sessions table...")
                cursor.execute("ALTER TABLE chat_sessions ADD COLUMN meta_data TEXT")
                print("Meta_data column added to chat_sessions table.")
            else:
                print("Meta_data column already exists in chat_sessions table.")
            
            # Check if meta_data column exists in chat_messages
            cursor.execute("SHOW COLUMNS FROM chat_messages LIKE 'meta_data'")
            meta_data_exists_messages = cursor.fetchone()
            
            if not meta_data_exists_messages:
                print("Adding meta_data column to chat_messages table...")
                cursor.execute("ALTER TABLE chat_messages ADD COLUMN meta_data TEXT")
                print("Meta_data column added to chat_messages table.")
            else:
                print("Meta_data column already exists in chat_messages table.")
            
            # Check if is_fortune column exists in chat_messages
            cursor.execute("SHOW COLUMNS FROM chat_messages LIKE 'is_fortune'")
            is_fortune_exists = cursor.fetchone()
            
            if not is_fortune_exists:
                print("Adding is_fortune column to chat_messages table...")
                cursor.execute("ALTER TABLE chat_messages ADD COLUMN is_fortune BOOLEAN DEFAULT 0")
                print("is_fortune column added to chat_messages table.")
            else:
                print("is_fortune column already exists in chat_messages table.")
        
        # Commit the changes
        conn.commit()
        print("Database altered successfully.")
    
    except Exception as e:
        print(f"Error altering database: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    alter_database() 