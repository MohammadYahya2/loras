import os
import sqlite3
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loras.settings')
django.setup()

# Connect to the SQLite database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the table already exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boutiqe_ordercancellation'")
table_exists = cursor.fetchone()

if table_exists:
    print("The boutiqe_ordercancellation table already exists.")
else:
    # Create the OrderCancellation table
    cursor.execute('''
    CREATE TABLE boutiqe_ordercancellation (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        order_id VARCHAR(50) NOT NULL,
        reason TEXT NOT NULL,
        phone VARCHAR(20) NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_approved BOOL NOT NULL DEFAULT 0,
        user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
    )
    ''')
    
    # Create an index on user_id for faster lookups
    cursor.execute('''
    CREATE INDEX boutiqe_ordercancellation_user_id_idx ON boutiqe_ordercancellation(user_id)
    ''')
    
    # Create an index on order_id for faster lookups
    cursor.execute('''
    CREATE INDEX boutiqe_ordercancellation_order_id_idx ON boutiqe_ordercancellation(order_id)
    ''')
    
    print("Successfully created the boutiqe_ordercancellation table.")

conn.commit()
conn.close() 