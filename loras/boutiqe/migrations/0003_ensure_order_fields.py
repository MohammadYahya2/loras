from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('boutiqe', '0002_create_order_table'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            PRAGMA foreign_keys=off;
            
            ALTER TABLE boutiqe_order RENAME TO boutiqe_order_old;
            
            CREATE TABLE IF NOT EXISTS "boutiqe_order" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "order_id" varchar(50) NOT NULL UNIQUE,
                "status" varchar(20) NOT NULL,
                "created_at" datetime NOT NULL,
                "paid_at" datetime NULL,
                "email" varchar(254) NULL,
                "shipping_address" text NULL,
                "phone_number" varchar(20) NULL,
                "user_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
            );
            
            INSERT OR IGNORE INTO boutiqe_order SELECT * FROM boutiqe_order_old;
            
            DROP TABLE boutiqe_order_old;
            
            CREATE TABLE IF NOT EXISTS "boutiqe_orderitem" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "quantity" integer unsigned NOT NULL,
                "order_id" integer NOT NULL REFERENCES "boutiqe_order" ("id") DEFERRABLE INITIALLY DEFERRED,
                "product_id" integer NOT NULL REFERENCES "boutiqe_product" ("id") DEFERRABLE INITIALLY DEFERRED
            );
            
            PRAGMA foreign_keys=on;
            """,
            reverse_sql=None
        ),
    ] 