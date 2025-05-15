import sqlite3
import os

# Specify the database path directly
db_path = "db.sqlite3"

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Connected to database at: {db_path}")
    
    # Get list of tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in database: {[table[0] for table in tables]}")
    
    # Try to fix the OrderItem table
    try:
        # Check if the boutiqe_orderitem table exists
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='boutiqe_orderitem';")
        if cursor.fetchone():
            # Check if the color_id column exists in the boutiqe_orderitem table
            cursor.execute("PRAGMA table_info(boutiqe_orderitem)")
            columns = [column[1] for column in cursor.fetchall()]
            
            print(f"Current columns in boutiqe_orderitem: {columns}")
            
            # Add missing columns if they don't exist
            if 'color_id' not in columns:
                print("Adding color_id column...")
                cursor.execute("ALTER TABLE boutiqe_orderitem ADD COLUMN color_id integer NULL")
            
            if 'size_id' not in columns:
                print("Adding size_id column...")
                cursor.execute("ALTER TABLE boutiqe_orderitem ADD COLUMN size_id integer NULL")
            
            if 'unit_price' not in columns:
                print("Adding unit_price column...")
                cursor.execute("ALTER TABLE boutiqe_orderitem ADD COLUMN unit_price decimal(10,2) NULL")
            
            if 'created_at' not in columns:
                print("Adding created_at column...")
                cursor.execute("ALTER TABLE boutiqe_orderitem ADD COLUMN created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP")
            
            # Verify the changes
            cursor.execute("PRAGMA table_info(boutiqe_orderitem)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Updated columns in boutiqe_orderitem: {columns}")
        else:
            print("Table boutiqe_orderitem does not exist")
    except Exception as e:
        print(f"Error updating boutiqe_orderitem: {e}")
    
    # Commit the changes
    conn.commit()
    print("Database changes committed.")
    
    # Close the connection
    conn.close()
    print("Database connection closed.")
    
except Exception as e:
    print(f"Error connecting to database: {e}") 