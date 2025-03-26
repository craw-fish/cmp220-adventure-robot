import sqlite3
import os

db_path = 'database/adventure_log.db'

# ensure database exists
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    try:
        # Try to connect to the database
        conn = sqlite3.connect(db_path)
        print("Connection successful!")

        # Test query (simple select)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        
        # Fetch the results of the query
        tables = cursor.fetchall()
        print("Tables in the database:", tables)

        # Close the connection
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"Database connection failed: {e}")
        