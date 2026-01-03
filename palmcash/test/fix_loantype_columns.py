import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Check and add missing columns to loans_loantype table
columns_to_add = [
    ('min_term_days', 'INT NULL'),
    ('max_term_days', 'INT NULL'),
    ('min_term_weeks', 'INT NULL'),
    ('max_term_weeks', 'INT NULL'),
]

print("Checking loans_loantype table columns...")
print("="*60)

for column_name, column_type in columns_to_add:
    cursor.execute(f"SHOW COLUMNS FROM loans_loantype LIKE '{column_name}'")
    if not cursor.fetchone():
        print(f"Adding {column_name} column...")
        cursor.execute(f'ALTER TABLE loans_loantype ADD COLUMN {column_name} {column_type}')
        print(f"✓ Added {column_name}")
    else:
        print(f"✓ {column_name} already exists")

print("\n" + "="*60)
print("✅ LoanType table schema fixed successfully!")
