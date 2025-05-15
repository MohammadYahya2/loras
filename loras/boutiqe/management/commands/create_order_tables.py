from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Creates the order and order item tables in the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating order tables...'))
        
        # Check if tables already exist
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boutiqe_order'")
            order_table_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boutiqe_orderitem'")
            orderitem_table_exists = cursor.fetchone() is not None
        
        if order_table_exists and orderitem_table_exists:
            self.stdout.write(self.style.WARNING('Order tables already exist!'))
            return
        
        with connection.cursor() as cursor:
            # Create boutiqe_order table if it doesn't exist
            if not order_table_exists:
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
                
                # Create index on user_id
                cursor.execute('''
                CREATE INDEX "boutiqe_order_user_id_idx" ON "boutiqe_order" ("user_id")
                ''')
                
                self.stdout.write(self.style.SUCCESS('Created boutiqe_order table'))
            
            # Create boutiqe_orderitem table if it doesn't exist
            if not orderitem_table_exists:
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
                
                # Create indexes
                cursor.execute('''
                CREATE INDEX "boutiqe_orderitem_color_id_idx" ON "boutiqe_orderitem" ("color_id")
                ''')
                cursor.execute('''
                CREATE INDEX "boutiqe_orderitem_order_id_idx" ON "boutiqe_orderitem" ("order_id")
                ''')
                cursor.execute('''
                CREATE INDEX "boutiqe_orderitem_product_id_idx" ON "boutiqe_orderitem" ("product_id")
                ''')
                cursor.execute('''
                CREATE INDEX "boutiqe_orderitem_size_id_idx" ON "boutiqe_orderitem" ("size_id")
                ''')
                
                self.stdout.write(self.style.SUCCESS('Created boutiqe_orderitem table'))
        
        self.stdout.write(self.style.SUCCESS('Order tables created successfully!')) 