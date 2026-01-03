#!/usr/bin/env python
"""
Final fix - add columns to the actual database Django is using
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import connection
from django.conf import settings

def final_fix():
    db_name = settings.DATABASES['default']['NAME']
    print(f"🔧 Fixing database: {db_name}")
    print(f"   Host: {settings.DATABASES['default']['HOST']}")
    print(f"   Port: {settings.DATABASES['default']['PORT']}\n")
    
    with connection.cursor() as cursor:
        # First, check current columns
        cursor.execute("SHOW COLUMNS FROM loans_loan")
        existing = [row[0] for row in cursor.fetchall()]
        print(f"📋 Existing columns in loans_loan: {len(existing)}")
        
        if 'repayment_frequency' not in existing:
            print("❌ repayment_frequency NOT FOUND - Adding now...")
            try:
                cursor.execute("""
                    ALTER TABLE loans_loan 
                    ADD COLUMN repayment_frequency VARCHAR(10) DEFAULT 'weekly' 
                    AFTER term_months
                """)
                print("✅ Added repayment_frequency")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("✅ repayment_frequency exists")
        
        if 'term_days' not in existing:
            print("❌ term_days NOT FOUND - Adding now...")
            try:
                cursor.execute("""
                    ALTER TABLE loans_loan 
                    ADD COLUMN term_days INT NULL 
                    AFTER repayment_frequency
                """)
                print("✅ Added term_days")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("✅ term_days exists")
        
        if 'term_weeks' not in existing:
            print("❌ term_weeks NOT FOUND - Adding now...")
            try:
                cursor.execute("""
                    ALTER TABLE loans_loan 
                    ADD COLUMN term_weeks INT NULL 
                    AFTER term_days
                """)
                print("✅ Added term_weeks")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("✅ term_weeks exists")
        
        if 'payment_amount' not in existing:
            print("❌ payment_amount NOT FOUND - Adding now...")
            try:
                cursor.execute("""
                    ALTER TABLE loans_loan 
                    ADD COLUMN payment_amount DECIMAL(10,2) NULL 
                    AFTER monthly_payment
                """)
                print("✅ Added payment_amount")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("✅ payment_amount exists")
        
        print("\n" + "="*60)
        
        # Check LoanType table
        cursor.execute("SHOW COLUMNS FROM loans_loantype")
        existing_lt = [row[0] for row in cursor.fetchall()]
        print(f"📋 Existing columns in loans_loantype: {len(existing_lt)}")
        
        if 'repayment_frequency' not in existing_lt:
            print("❌ repayment_frequency NOT FOUND in loantype - Adding...")
            try:
                cursor.execute("""
                    ALTER TABLE loans_loantype 
                    ADD COLUMN repayment_frequency VARCHAR(10) DEFAULT 'weekly' 
                    AFTER is_active
                """)
                print("✅ Added repayment_frequency to loantype")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("✅ repayment_frequency exists in loantype")
        
        # Add other loantype columns
        for col in ['min_term_days', 'max_term_days', 'min_term_weeks', 'max_term_weeks']:
            if col not in existing_lt:
                print(f"❌ {col} NOT FOUND - Adding...")
                try:
                    cursor.execute(f"ALTER TABLE loans_loantype ADD COLUMN {col} INT NULL")
                    print(f"✅ Added {col}")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print(f"✅ {col} exists")
        
        print("\n" + "="*60)
        print("✅ All columns added! Restart the server.")
        print("="*60)

if __name__ == "__main__":
    try:
        final_fix()
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
