import sqlite3
import os
import sys

# Path to the SQLite database
db_path = 'db.sqlite3'

# Check if the database exists
if not os.path.exists(db_path):
    print(f"Database '{db_path}' not found. Make sure you're in the right directory.")
    sys.exit(1)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the boutiqe_order table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boutiqe_order'")
if not cursor.fetchone():
    print("Table 'boutiqe_order' not found in the database.")
    conn.close()
    sys.exit(1)

# Check if the contact_info_id column already exists
cursor.execute("PRAGMA table_info(boutiqe_order)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'contact_info_id' in column_names:
    print("Column 'contact_info_id' already exists in the 'boutiqe_order' table.")
else:
    # Get the columns from the current table
    print("Adding 'contact_info_id' column to 'boutiqe_order' table...")
    
    try:
        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys=off")
        
        # Start a transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Create a new table with the contact_info_id column
        cursor.execute("""
        CREATE TABLE boutiqe_order_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            order_id VARCHAR(50) NOT NULL UNIQUE,
            status VARCHAR(20) NOT NULL,
            created_at DATETIME NOT NULL,
            paid_at DATETIME NULL,
            email VARCHAR(254) NULL,
            shipping_address TEXT NULL,
            phone_number VARCHAR(20) NULL,
            user_id INTEGER NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
            session_key VARCHAR(40) NULL,
            contact_info_id INTEGER NULL REFERENCES boutiqe_contactinfo(id) DEFERRABLE INITIALLY DEFERRED
        )
        """)
        
        # Copy data from the old table to the new one
        cursor.execute("""
        INSERT INTO boutiqe_order_new (id, order_id, status, created_at, paid_at, email, shipping_address, 
        phone_number, user_id, session_key)
        SELECT id, order_id, status, created_at, paid_at, email, shipping_address, phone_number, user_id, session_key
        FROM boutiqe_order
        """)
        
        # Drop the old table
        cursor.execute("DROP TABLE boutiqe_order")
        
        # Rename the new table to the original name
        cursor.execute("ALTER TABLE boutiqe_order_new RENAME TO boutiqe_order")
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS boutiqe_order_user_id_idx ON boutiqe_order(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS boutiqe_order_contact_info_id_idx ON boutiqe_order(contact_info_id)")
        
        # Commit the transaction
        cursor.execute("COMMIT")
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=on")
        
        print("Column 'contact_info_id' added successfully.")
    except Exception as e:
        # Roll back in case of error
        cursor.execute("ROLLBACK")
        print(f"Error adding column: {e}")

# Close the connection
conn.close()

print("Database fix completed.") 