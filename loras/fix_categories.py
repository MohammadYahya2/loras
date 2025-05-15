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
from boutiqe.models import Category

def fix_categories():
    # عرض جميع الفئات المسجلة في قاعدة البيانات
    categories = Category.objects.all()
    print(f"عدد الفئات الموجودة في قاعدة البيانات: {categories.count()}")
    
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category.name} (slug: {category.slug}, نشطة: {category.is_active})")
    
    # التأكد من أن جميع الفئات نشطة
    inactive_categories = Category.objects.filter(is_active=False)
    if inactive_categories.exists():
        print(f"\nتم العثور على {inactive_categories.count()} فئة غير نشطة. جاري تنشيطها...")
        inactive_categories.update(is_active=True)
        print("تم تنشيط جميع الفئات.")
    
    # فحص الأخطاء المحتملة في الفئات
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys=off;")
        
        # البحث عن أي مشاكل في جدول الفئات
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchall()
        print(f"\nنتيجة فحص سلامة قاعدة البيانات: {integrity_result}")
        
        # إصلاح مشكلة تكرار slugs إن وجدت
        cursor.execute("SELECT slug, COUNT(*) FROM boutiqe_category GROUP BY slug HAVING COUNT(*) > 1;")
        duplicate_slugs = cursor.fetchall()
        
        if duplicate_slugs:
            print(f"\nتم العثور على {len(duplicate_slugs)} slug مكرر. جاري الإصلاح...")
            for slug, count in duplicate_slugs:
                print(f"  - {slug}: {count} مرات")
                # إصلاح السلاقات المكررة بإضافة أرقام إليها
                cursor.execute(f"SELECT id, name FROM boutiqe_category WHERE slug = '{slug}';")
                dupes = cursor.fetchall()
                for i, (id, name) in enumerate(dupes[1:], 1):  # ترك الأول كما هو
                    new_slug = f"{slug}-{i}"
                    print(f"    تغيير slug للفئة {name} (ID: {id}) من '{slug}' إلى '{new_slug}'")
                    cursor.execute(f"UPDATE boutiqe_category SET slug = '{new_slug}' WHERE id = {id};")
        
        cursor.execute("PRAGMA foreign_keys=on;")
    
    # عرض النتائج بعد الإصلاح
    updated_categories = Category.objects.all()
    print(f"\nعدد الفئات بعد الإصلاح: {updated_categories.count()}")
    
    for i, category in enumerate(updated_categories, 1):
        print(f"{i}. {category.name} (slug: {category.slug}, نشطة: {category.is_active})")
    
    print("\nتم الإصلاح بنجاح.")

if __name__ == "__main__":
    fix_categories() 