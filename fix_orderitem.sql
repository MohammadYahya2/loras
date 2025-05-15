-- التحقق من وجود الأعمدة المطلوبة وإضافتها إذا لم تكن موجودة
PRAGMA foreign_keys=off;

-- إنشاء جدول جديد يحتوي على جميع الأعمدة المطلوبة
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

-- نسخ البيانات من الجدول القديم إلى الجدول الجديد
INSERT OR IGNORE INTO boutiqe_orderitem_new (id, quantity, order_id, product_id)
SELECT id, quantity, order_id, product_id FROM boutiqe_orderitem;

-- تحديث حقل created_at لجميع الصفوف
UPDATE boutiqe_orderitem_new SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- حذف الجدول القديم
DROP TABLE IF EXISTS boutiqe_orderitem;

-- إعادة تسمية الجدول الجديد إلى الاسم الأصلي
ALTER TABLE boutiqe_orderitem_new RENAME TO boutiqe_orderitem;

-- إنشاء الفهارس الضرورية
CREATE INDEX IF NOT EXISTS "boutiqe_orderitem_order_id_idx" ON "boutiqe_orderitem" ("order_id");
CREATE INDEX IF NOT EXISTS "boutiqe_orderitem_product_id_idx" ON "boutiqe_orderitem" ("product_id");
CREATE INDEX IF NOT EXISTS "boutiqe_orderitem_color_id_idx" ON "boutiqe_orderitem" ("color_id");
CREATE INDEX IF NOT EXISTS "boutiqe_orderitem_size_id_idx" ON "boutiqe_orderitem" ("size_id");

PRAGMA foreign_keys=on; 