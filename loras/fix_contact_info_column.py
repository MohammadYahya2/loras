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
print(f"Current columns in boutiqe_order: {column_names}")

if 'contact_info_id' in column_names:
    print("Column 'contact_info_id' already exists in the 'boutiqe_order' table.")
else:
    # Get the columns from the current table
    print("Adding 'contact_info_id' column to 'boutiqe_order' table...")
    
    try:
        # Try simpler approach first - just alter the table 
        # This works for SQLite 3.20+ (2017 and later)
        cursor.execute("ALTER TABLE boutiqe_order ADD COLUMN contact_info_id INTEGER NULL REFERENCES boutiqe_contactinfo(id)")
        
        # Commit the changes
        conn.commit()
        
        # Check if the column was added
        cursor.execute("PRAGMA table_info(boutiqe_order)")
        new_columns = cursor.fetchall()
        new_column_names = [column[1] for column in new_columns]
        
        if 'contact_info_id' in new_column_names:
            print("Column 'contact_info_id' added successfully with ALTER TABLE.")
        else:
            print("Failed to add column with ALTER TABLE. This might be due to an older SQLite version.")
            print("Attempting alternative approach...")
            
            # Disable foreign key constraints temporarily
            cursor.execute("PRAGMA foreign_keys=off")
            
            # Start a transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Get the actual column names from the table
            cursor.execute("PRAGMA table_info(boutiqe_order)")
            existing_columns = cursor.fetchall()
            existing_column_names = [column[1] for column in existing_columns]
            
            # Create comma-separated list of columns
            columns_list = ', '.join(existing_column_names)
            
            # Create a new table with the contact_info_id column
            create_table_sql = f"""
            CREATE TABLE boutiqe_order_new (
                {', '.join([f'{col[1]} {col[2]}' for col in existing_columns])},
                contact_info_id INTEGER NULL REFERENCES boutiqe_contactinfo(id) DEFERRABLE INITIALLY DEFERRED
            )
            """
            cursor.execute(create_table_sql)
            
            # Copy data from the old table to the new one
            cursor.execute(f"""
            INSERT INTO boutiqe_order_new ({columns_list})
            SELECT {columns_list} FROM boutiqe_order
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
            
            print("Column 'contact_info_id' added successfully with table recreation.")
    except Exception as e:
        # Roll back in case of error
        try:
            cursor.execute("ROLLBACK")
        except:
            pass
        print(f"Error adding column: {e}")

# Close the connection
conn.close()

print("Database fix completed.") 