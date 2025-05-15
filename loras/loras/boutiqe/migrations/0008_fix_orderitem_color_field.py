from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('boutiqe', '0007_alter_category_options_category_created_at_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            PRAGMA foreign_keys=off;
            
            -- Create a new table with all the required columns
            CREATE TABLE boutiqe_orderitem_new (
                id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                quantity integer unsigned NOT NULL,
                order_id integer NOT NULL REFERENCES boutiqe_order(id) DEFERRABLE INITIALLY DEFERRED,
                product_id integer NOT NULL REFERENCES boutiqe_product(id) DEFERRABLE INITIALLY DEFERRED,
                color_id integer NULL,
                size_id integer NULL,
                unit_price decimal(10,2) NULL,
                created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Copy data from old table to new table
            INSERT INTO boutiqe_orderitem_new (id, quantity, order_id, product_id)
            SELECT id, quantity, order_id, product_id FROM boutiqe_orderitem;
            
            -- Drop the old table
            DROP TABLE boutiqe_orderitem;
            
            -- Rename the new table to the original name
            ALTER TABLE boutiqe_orderitem_new RENAME TO boutiqe_orderitem;
            
            PRAGMA foreign_keys=on;
            """,
            reverse_sql="""
            PRAGMA foreign_keys=off;
            
            -- Create a table without the added columns
            CREATE TABLE boutiqe_orderitem_old (
                id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                quantity integer unsigned NOT NULL,
                order_id integer NOT NULL REFERENCES boutiqe_order(id) DEFERRABLE INITIALLY DEFERRED,
                product_id integer NOT NULL REFERENCES boutiqe_product(id) DEFERRABLE INITIALLY DEFERRED
            );
            
            -- Copy data back
            INSERT INTO boutiqe_orderitem_old (id, quantity, order_id, product_id)
            SELECT id, quantity, order_id, product_id FROM boutiqe_orderitem;
            
            -- Drop the new table
            DROP TABLE boutiqe_orderitem;
            
            -- Rename the old table back to the original name
            ALTER TABLE boutiqe_orderitem_old RENAME TO boutiqe_orderitem;
            
            PRAGMA foreign_keys=on;
            """
        ),
    ] 