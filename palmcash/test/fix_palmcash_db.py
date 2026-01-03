#!/usr/bin/env python
"""
Add columns to palmcash_db specifically
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import connection
from django.conf import settings

def fix_palmcash_db():
    print(f"🔧 Fixing database: {settings.DATABASES['default']['NAME']}")
    print(f"   Host: {settings.DATABASES['default']['HOST']}")
    print(f"   Port: {settings.DATABASES['default']['PORT']}\n")
    
    with connection.cursor() as cursor:
        # Add columns to loans_loan
        try:
            cursor.execute("ALTER TABLE loans_loan ADD COLUMN repayment_frequency VARCHAR(10) DEFAULT 'weekly'")
            print("✅ Added repayment_frequency to loans_loan")
        except Exception as e:
            if '1060' in str(e):  # Duplicate column
                print("ℹ️  repayment_frequency already exists in loans_loan")
            else:
                print(f"❌ Error adding repayment_frequency: {e}")
        
        try:
            cursor.execute("ALTER TABLE loans_loan ADD COLUMN term_days INT NULL")
            print("✅ Added term_days to loans_loan")
        except Exception as e:
            if '1060' in str(e):
                print("ℹ️  term_days already exists in loans_loan")
            else:
                print(f"❌ Error adding term_days: {e}")
        
        try:
            cursor.execute("ALTER TABLE loans_loan ADD COLUMN term_weeks INT NULL")
            print("✅ Added term_weeks to loans_loan")
        except Exception as e:
            if '1060' in str(e):
                print("ℹ️  term_weeks already exists in loans_loan")
            else:
                print(f"❌ Error adding term_weeks: {e}")
        
        try:
            cursor.execute("ALTER TABLE loans_loan ADD COLUMN payment_amount DECIMAL(10,2) NULL")
            print("✅ Added payment_amount to loans_loan")
        except Exception as e:
            if '1060' in str(e):
                print("ℹ️  payment_amount already exists in loans_loan")
            else:
                print(f"❌ Error adding payment_amount: {e}")
        
        print()
        
        # Add columns to loans_loantype
        try:
            cursor.execute("ALTER TABLE loans_loantype ADD COLUMN repayment_frequency VARCHAR(10) DEFAULT 'weekly'")
            print("✅ Added repayment_frequency to loans_loantype")
        except Exception as e:
            if '1060' in str(e):
                print("ℹ️  repayment_frequency already exists in loans_loantype")
            else:
                print(f"❌ Error: {e}")
        
        try:
            cursor.execute("ALTER TABLE loans_loantype ADD COLUMN min_term_days INT NULL")
            print("✅ Added min_term_days to loans_loantype")
        except Exception as e:
            if '1060' in str(e):
                print("ℹ️  min_term_days already exists")
            else:
                print(f"❌ Error: {e}")
        
        try:
            cursor.execute("ALTER TABLE loans_loantype ADD COLUMN max_term_days INT NULL")
            print("✅ Added max_term_days to loans_loantype")
        except Exception as e:
            if '1060' in str(e):
                print("ℹ️  max_term_days already exists")
            else:
                print(f"❌ Error: {e}")
        
        try:
            cursor.execute("ALTER TABLE loans_loantype ADD COLUMN min_term_weeks INT NULL")
            print("✅ Added min_term_weeks to loans_loantype")
        except Exception as e:
            if '1060' in str(e):
                print("ℹ️  min_term_weeks already exists")
            else:
                print(f"❌ Error: {e}")
        
        try:
            cursor.execute("ALTER TABLE loans_loantype ADD COLUMN max_term_weeks INT NULL")
            print("✅ Added max_term_weeks to loans_loantype")
        except Exception as e:
            if '1060' in str(e):
                print("ℹ️  max_term_weeks already exists")
            else:
                print(f"❌ Error: {e}")
    
    print("\n✅ Done! Restart the server.")

if __name__ == "__main__":
    try:
        fix_palmcash_db()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
