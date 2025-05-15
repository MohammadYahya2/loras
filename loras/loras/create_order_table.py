import os
import sys
import django
import sqlite3

# Add the project directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loras.settings')
django.setup()

# Now we can import Django models
from boutiqe.models import Order

# Get the database path from Django settings
from django.conf import settings
db_path = settings.DATABASES['default']['NAME']

print(f"Database path: {db_path}")

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boutiqe_order'")
if cursor.fetchone():
    print("Table 'boutiqe_order' already exists.")
else:
    print("Table 'boutiqe_order' does not exist. Creating it...")
    
    # Get the SQL from Django's schema editor
    from django.db import connection
    
    # This will create the necessary SQL statements for the Order model
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Order)
    
    print("Table 'boutiqe_order' created successfully.")

# Close connection
conn.close()
print("Done.") 