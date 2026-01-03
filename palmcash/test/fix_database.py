import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Check if columns exist first
cursor.execute("SHOW COLUMNS FROM loans_loan LIKE 'upfront_payment_required'")
if not cursor.fetchone():
    print("Adding upfront_payment_required column...")
    cursor.execute('ALTER TABLE loans_loan ADD COLUMN upfront_payment_required DECIMAL(12, 2) NULL')
    print("✓ Added upfront_payment_required")
else:
    print("✓ upfront_payment_required already exists")

cursor.execute("SHOW COLUMNS FROM loans_loan LIKE 'upfront_payment_paid'")
if not cursor.fetchone():
    print("Adding upfront_payment_paid column...")
    cursor.execute('ALTER TABLE loans_loan ADD COLUMN upfront_payment_paid DECIMAL(12, 2) DEFAULT 0 NOT NULL')
    print("✓ Added upfront_payment_paid")
else:
    print("✓ upfront_payment_paid already exists")

cursor.execute("SHOW COLUMNS FROM loans_loan LIKE 'upfront_payment_date'")
if not cursor.fetchone():
    print("Adding upfront_payment_date column...")
    cursor.execute('ALTER TABLE loans_loan ADD COLUMN upfront_payment_date DATETIME NULL')
    print("✓ Added upfront_payment_date")
else:
    print("✓ upfront_payment_date already exists")

cursor.execute("SHOW COLUMNS FROM loans_loan LIKE 'upfront_payment_verified'")
if not cursor.fetchone():
    print("Adding upfront_payment_verified column...")
    cursor.execute('ALTER TABLE loans_loan ADD COLUMN upfront_payment_verified TINYINT(1) DEFAULT 0 NOT NULL')
    print("✓ Added upfront_payment_verified")
else:
    print("✓ upfront_payment_verified already exists")

print("\n✅ Database schema fixed successfully!")
