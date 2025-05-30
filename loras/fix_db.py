import os
import django
import sys
import sqlite3

# إضافة مسار المشروع إلى Python path
sys.path.insert(0, os.path.abspath('.'))

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loras.settings')
django.setup()

# استيراد النماذج اللازمة
from django.db import connection
from django.utils import timezone

def fix_database():
    with connection.cursor() as cursor:
        # التحقق من وجود جدول OrderItem
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='boutiqe_orderitem';
        """)
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("جدول 'boutiqe_orderitem' غير موجود.")
            return
        
        # عرض هيكل الجدول الحالي
        cursor.execute("PRAGMA table_info(boutiqe_orderitem);")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        print(f"الأعمدة الحالية في جدول boutiqe_orderitem: {column_names}")
        
        try:
            # إنشاء جدول جديد بكل الأعمدة المطلوبة
            print("إنشاء جدول جديد...")
            cursor.execute("PRAGMA foreign_keys=off;")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "boutiqe_orderitem_new" (
                    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    "quantity" integer unsigned NOT NULL,
                    "order_id" integer NOT NULL REFERENCES "boutiqe_order" ("id") DEFERRABLE INITIALLY DEFERRED,
                    "product_id" integer NOT NULL REFERENCES "boutiqe_product" ("id") DEFERRABLE INITIALLY DEFERRED,
                    "color_id" integer NULL REFERENCES "boutiqe_color" ("id") DEFERRABLE INITIALLY DEFERRED,
                    "size_id" integer NULL REFERENCES "boutiqe_size" ("id") DEFERRABLE INITIALLY DEFERRED,
                    "unit_price" decimal(10,2) NULL,
                    "created_at" datetime NULL
                );
            """)
            
            # نسخ البيانات
            print("نسخ البيانات من الجدول القديم...")
            cursor.execute("""
                INSERT OR IGNORE INTO boutiqe_orderitem_new (id, quantity, order_id, product_id)
                SELECT id, quantity, order_id, product_id FROM boutiqe_orderitem;
            """)
            
            # تعيين قيمة لحقل created_at
            current_time = timezone.now().isoformat()
            cursor.execute(f"UPDATE boutiqe_orderitem_new SET created_at = '{current_time}';")
            
            # حذف الجدول القديم
            print("حذف الجدول القديم...")
            cursor.execute("DROP TABLE boutiqe_orderitem;")
            
            # إعادة تسمية الجدول الجديد
            print("إعادة تسمية الجدول الجديد...")
            cursor.execute("ALTER TABLE boutiqe_orderitem_new RENAME TO boutiqe_orderitem;")
            
            # إنشاء الفهارس
            cursor.execute("CREATE INDEX IF NOT EXISTS boutiqe_orderitem_order_id_idx ON boutiqe_orderitem (order_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS boutiqe_orderitem_product_id_idx ON boutiqe_orderitem (product_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS boutiqe_orderitem_color_id_idx ON boutiqe_orderitem (color_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS boutiqe_orderitem_size_id_idx ON boutiqe_orderitem (size_id);")
            
            cursor.execute("PRAGMA foreign_keys=on;")
            
            # التحقق من الإصلاح
            cursor.execute("PRAGMA table_info(boutiqe_orderitem);")
            updated_columns = cursor.fetchall()
            updated_column_names = [column[1] for column in updated_columns]
            print(f"الأعمدة المحدثة في جدول boutiqe_orderitem: {updated_column_names}")
            
            print("تم تحديث قاعدة البيانات بنجاح.")
            
        except Exception as e:
            print(f"حدث خطأ أثناء تحديث قاعدة البيانات: {e}")

    # Path to the SQLite database
    db_path = 'db.sqlite3'

    # Check if the database exists
    if not os.path.exists(db_path):
        print(f"Database '{db_path}' not found. Make sure you're in the right directory.")
        return

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the boutiqe_order table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boutiqe_order'")
    if not cursor.fetchone():
        print("Table 'boutiqe_order' not found in the database.")
        conn.close()
        return

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

def add_contact_info_column():
    """
    Add contact_info_id column to the boutiqe_order table if it doesn't exist
    """
    print("Starting database fix script...")
    
    # Get the path to the db.sqlite3 file (it should be in the current directory)
    db_path = 'db.sqlite3'
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the contact_info_id column already exists
        cursor.execute("PRAGMA table_info(boutiqe_order)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'contact_info_id' in column_names:
            print("Column 'contact_info_id' already exists in boutiqe_order table. No changes needed.")
            conn.close()
            return True
        
        # Add the contact_info_id column to the boutiqe_order table
        print("Adding 'contact_info_id' column to boutiqe_order table...")
        cursor.execute("ALTER TABLE boutiqe_order ADD COLUMN contact_info_id INTEGER NULL REFERENCES boutiqe_contactinfo(id)")
        
        # Commit the changes
        conn.commit()
        print("Column added successfully!")
        
        # Close the connection
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    fix_database()
    success = add_contact_info_column()
    
    if success:
        print("Database structure updated successfully.")
        sys.exit(0)
    else:
        print("Failed to update database structure.")
        sys.exit(1) 