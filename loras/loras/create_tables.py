from django.db import connection

def create_tables():
    with connection.cursor() as cursor:
        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boutiqe_order'")
        order_exists = cursor.fetchone()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boutiqe_orderitem'")
        orderitem_exists = cursor.fetchone()
        
        if not order_exists:
            print('Creating boutiqe_order table...')
            cursor.execute('''
            CREATE TABLE "boutiqe_order" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "order_id" varchar(50) NOT NULL UNIQUE,
                "status" varchar(20) NOT NULL,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "shipping_address" text NOT NULL,
                "shipping_city" varchar(100) NOT NULL,
                "shipping_country" varchar(100) NOT NULL,
                "shipping_phone" varchar(20) NOT NULL,
                "shipping_cost" decimal NOT NULL,
                "discount_amount" decimal NOT NULL,
                "subtotal" decimal NOT NULL,
                "total" decimal NOT NULL,
                "payment_method" varchar(50) NOT NULL,
                "is_paid" bool NOT NULL,
                "paid_at" datetime NULL,
                "currency" varchar(3) NOT NULL,
                "exchange_rate" decimal NOT NULL,
                "notes" text NULL,
                "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
            )
            ''')
            print('Successfully created boutiqe_order table')
        else:
            print('boutiqe_order table already exists')
        
        if not orderitem_exists:
            print('Creating boutiqe_orderitem table...')
            cursor.execute('''
            CREATE TABLE "boutiqe_orderitem" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "quantity" integer NOT NULL,
                "price" decimal NOT NULL,
                "total" decimal NOT NULL,
                "color_id" integer NULL REFERENCES "boutiqe_color" ("id") DEFERRABLE INITIALLY DEFERRED,
                "order_id" integer NOT NULL REFERENCES "boutiqe_order" ("id") DEFERRABLE INITIALLY DEFERRED,
                "product_id" integer NOT NULL REFERENCES "boutiqe_product" ("id") DEFERRABLE INITIALLY DEFERRED,
                "size_id" integer NULL REFERENCES "boutiqe_size" ("id") DEFERRABLE INITIALLY DEFERRED
            )
            ''')
            print('Successfully created boutiqe_orderitem table')
        else:
            print('boutiqe_orderitem table already exists')

# Call the function when this module is loaded in Django shell
create_tables() 