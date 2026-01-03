#!/usr/bin/env python
"""
Verify and fix database columns for daily/weekly system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import connection

def verify_and_fix():
    print("🔍 Checking database columns...\n")
    
    with connection.cursor() as cursor:
        # Check loans_loan table
        cursor.execute("SHOW COLUMNS FROM loans_loan")
        loan_columns = [row[0] for row in cursor.fetchall()]
        
        print("📋 Current loans_loan columns:")
        for col in sorted(loan_columns):
            print(f"  - {col}")
        print()
        
        # Check if new columns exist
        needed_columns = ['repayment_frequency', 'term_days', 'term_weeks', 'payment_amount']
        missing = [col for col in needed_columns if col not in loan_columns]
        
        if missing:
            print(f"❌ Missing columns in loans_loan: {', '.join(missing)}")
            print("   Adding them now...\n")
            
            if 'repayment_frequency' in missing:
                cursor.execute("ALTER TABLE loans_loan ADD COLUMN repayment_frequency VARCHAR(10) DEFAULT 'weekly' AFTER term_months")
                print("✅ Added repayment_frequency")
            
            if 'term_days' in missing:
                cursor.execute("ALTER TABLE loans_loan ADD COLUMN term_days INT NULL AFTER repayment_frequency")
                print("✅ Added term_days")
            
            if 'term_weeks' in missing:
                cursor.execute("ALTER TABLE loans_loan ADD COLUMN term_weeks INT NULL AFTER term_days")
                print("✅ Added term_weeks")
            
            if 'payment_amount' in missing:
                cursor.execute("ALTER TABLE loans_loan ADD COLUMN payment_amount DECIMAL(10,2) NULL AFTER monthly_payment")
                print("✅ Added payment_amount")
        else:
            print("✅ All required columns exist in loans_loan")
        
        print()
        
        # Check loans_loantype table
        cursor.execute("SHOW COLUMNS FROM loans_loantype")
        loantype_columns = [row[0] for row in cursor.fetchall()]
        
        print("📋 Current loans_loantype columns:")
        for col in sorted(loantype_columns):
            print(f"  - {col}")
        print()
        
        needed_loantype_columns = ['repayment_frequency', 'min_term_days', 'max_term_days', 'min_term_weeks', 'max_term_weeks']
        missing_loantype = [col for col in needed_loantype_columns if col not in loantype_columns]
        
        if missing_loantype:
            print(f"❌ Missing columns in loans_loantype: {', '.join(missing_loantype)}")
            print("   Adding them now...\n")
            
            if 'repayment_frequency' in missing_loantype:
                cursor.execute("ALTER TABLE loans_loantype ADD COLUMN repayment_frequency VARCHAR(10) DEFAULT 'weekly' AFTER is_active")
                print("✅ Added repayment_frequency to loantype")
            
            if 'min_term_days' in missing_loantype:
                cursor.execute("ALTER TABLE loans_loantype ADD COLUMN min_term_days INT NULL AFTER min_term_months")
                print("✅ Added min_term_days")
            
            if 'max_term_days' in missing_loantype:
                cursor.execute("ALTER TABLE loans_loantype ADD COLUMN max_term_days INT NULL AFTER min_term_days")
                print("✅ Added max_term_days")
            
            if 'min_term_weeks' in missing_loantype:
                cursor.execute("ALTER TABLE loans_loantype ADD COLUMN min_term_weeks INT NULL AFTER max_term_days")
                print("✅ Added min_term_weeks")
            
            if 'max_term_weeks' in missing_loantype:
                cursor.execute("ALTER TABLE loans_loantype ADD COLUMN max_term_weeks INT NULL AFTER min_term_weeks")
                print("✅ Added max_term_weeks")
        else:
            print("✅ All required columns exist in loans_loantype")
    
    print("\n" + "="*60)
    print("✅ Database verification and fix complete!")
    print("="*60)

if __name__ == "__main__":
    try:
        verify_and_fix()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
