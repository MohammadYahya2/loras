import os
import django
import sys

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

if __name__ == "__main__":
    fix_database() 