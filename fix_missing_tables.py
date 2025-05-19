import os
import django
import sys

# Add the project path to Python path
sys.path.insert(0, os.path.abspath('.'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loras.loras.settings')
django.setup()

from django.db import connection
from django.utils import timezone
import traceback

def fix_database():
    with connection.cursor() as cursor:
        try:
            print("Checking tables and fixing issues...")
            cursor.execute("PRAGMA foreign_keys=off;")
            
            # Check if boutiqe_order table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='boutiqe_order';
            """)
            order_table_exists = cursor.fetchone()
            
            if not order_table_exists:
                print("Creating 'boutiqe_order' table...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS "boutiqe_order" (
                        "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "status" varchar(50) NOT NULL,
                        "created_at" datetime NOT NULL,
                        "updated_at" datetime NOT NULL,
                        "total_price" decimal(10, 2) NOT NULL,
                        "user_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
                        "session_key" varchar(40) NULL,
                        "payment_method" varchar(50) NOT NULL,
                        "shipping_address" text NULL,
                        "tracking_number" varchar(100) NULL,
                        "notes" text NULL,
                        "shipping_fee" decimal(10, 2) NULL,
                        "discount_amount" decimal(10, 2) NULL
                    );
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS boutiqe_order_user_id_idx ON boutiqe_order (user_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS boutiqe_order_session_key_idx ON boutiqe_order (session_key);")
                
                print("'boutiqe_order' table created successfully.")
            
            # Check if field 'session_key' exists in Wishlist table
            cursor.execute("PRAGMA table_info(boutiqe_wishlist);")
            wishlist_columns = cursor.fetchall()
            wishlist_column_names = [column[1] for column in wishlist_columns]
            
            if 'session_key' not in wishlist_column_names:
                print("Adding 'session_key' field to 'boutiqe_wishlist' table...")
                cursor.execute("""
                    ALTER TABLE boutiqe_wishlist 
                    ADD COLUMN session_key varchar(40) NULL;
                """)
                print("Field added successfully.")
            
            # Update constraints
            print("Ensuring proper constraints on wishlist table...")
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS unique_user_product_wishlist
                ON boutiqe_wishlist (user_id, product_id)
                WHERE user_id IS NOT NULL;
            """)
            
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS unique_session_product_wishlist
                ON boutiqe_wishlist (session_key, product_id)
                WHERE session_key IS NOT NULL;
            """)
            
            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys=on;")
            
            print("Database updated successfully.")
            
        except Exception as e:
            print(f"Error updating database: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    fix_database() 