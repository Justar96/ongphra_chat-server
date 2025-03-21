import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "94.237.66.12")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "admin_gpt_chat")
DB_PASSWORD = os.getenv("DB_PASSWORD", "R&7sn6]S(}0.!3Lu")
DB_NAME = os.getenv("DB_NAME", "gpt_log")

def check_database_structure():
    """Check the structure of the MariaDB database."""
    try:
        # Connect to the database
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"Successfully connected to MariaDB on {DB_HOST}")
        
        with connection.cursor() as cursor:
            # List tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print("\nDatabase Tables:")
            for table in tables:
                table_name = list(table.values())[0]
                print(f"- {table_name}")
                
                # Show table structure
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                print(f"\nStructure of {table_name}:")
                for column in columns:
                    print(f"  {column['Field']} - {column['Type']} - Null: {column['Null']} - Key: {column['Key']} - Default: {column['Default']}")
                
                # Show row count
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()
                print(f"\n  Row count: {count['count']}\n")
        
        connection.close()
        print("Connection closed")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_database_structure() 