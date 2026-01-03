#!/usr/bin/env python
"""
Script to update Palm Cash to Daily/Weekly loan system
This adds the necessary fields for daily and weekly repayment schedules
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import connection

def add_repayment_frequency_fields():
    """Add repayment frequency fields to LoanType and Loan models"""
    
    print("🌴 Updating Palm Cash to Daily/Weekly System...\n")
    
    with connection.cursor() as cursor:
        # Check if columns exist before adding
        cursor.execute("SHOW COLUMNS FROM loans_loantype LIKE 'repayment_frequency'")
        if not cursor.fetchone():
            print("✅ Adding repayment_frequency to LoanType...")
            cursor.execute("""
                ALTER TABLE loans_loantype 
                ADD COLUMN repayment_frequency VARCHAR(10) DEFAULT 'weekly' AFTER is_active
            """)
        else:
            print("ℹ️  repayment_frequency already exists in LoanType")
        
        cursor.execute("SHOW COLUMNS FROM loans_loantype LIKE 'max_term_days'")
        if not cursor.fetchone():
            print("✅ Adding max_term_days to LoanType...")
            cursor.execute("""
                ALTER TABLE loans_loantype 
                ADD COLUMN max_term_days INT DEFAULT NULL AFTER max_term_months
            """)
        else:
            print("ℹ️  max_term_days already exists in LoanType")
        
        cursor.execute("SHOW COLUMNS FROM loans_loantype LIKE 'min_term_days'")
        if not cursor.fetchone():
            print("✅ Adding min_term_days to LoanType...")
            cursor.execute("""
                ALTER TABLE loans_loantype 
                ADD COLUMN min_term_days INT DEFAULT NULL AFTER min_term_months
            """)
        else:
            print("ℹ️  min_term_days already exists in LoanType")
        
        cursor.execute("SHOW COLUMNS FROM loans_loantype LIKE 'max_term_weeks'")
        if not cursor.fetchone():
            print("✅ Adding max_term_weeks to LoanType...")
            cursor.execute("""
                ALTER TABLE loans_loantype 
                ADD COLUMN max_term_weeks INT DEFAULT NULL AFTER max_term_days
            """)
        else:
            print("ℹ️  max_term_weeks already exists in LoanType")
        
        cursor.execute("SHOW COLUMNS FROM loans_loantype LIKE 'min_term_weeks'")
        if not cursor.fetchone():
            print("✅ Adding min_term_weeks to LoanType...")
            cursor.execute("""
                ALTER TABLE loans_loantype 
                ADD COLUMN min_term_weeks INT DEFAULT NULL AFTER min_term_days
            """)
        else:
            print("ℹ️  min_term_weeks already exists in LoanType")
        
        # Update Loan table
        cursor.execute("SHOW COLUMNS FROM loans_loan LIKE 'repayment_frequency'")
        if not cursor.fetchone():
            print("✅ Adding repayment_frequency to Loan...")
            cursor.execute("""
                ALTER TABLE loans_loan 
                ADD COLUMN repayment_frequency VARCHAR(10) DEFAULT 'weekly' AFTER term_months
            """)
        else:
            print("ℹ️  repayment_frequency already exists in Loan")
        
        cursor.execute("SHOW COLUMNS FROM loans_loan LIKE 'term_days'")
        if not cursor.fetchone():
            print("✅ Adding term_days to Loan...")
            cursor.execute("""
                ALTER TABLE loans_loan 
                ADD COLUMN term_days INT DEFAULT NULL AFTER term_months
            """)
        else:
            print("ℹ️  term_days already exists in Loan")
        
        cursor.execute("SHOW COLUMNS FROM loans_loan LIKE 'term_weeks'")
        if not cursor.fetchone():
            print("✅ Adding term_weeks to Loan...")
            cursor.execute("""
                ALTER TABLE loans_loan 
                ADD COLUMN term_weeks INT DEFAULT NULL AFTER term_days
            """)
        else:
            print("ℹ️  term_weeks already exists in Loan")
        
        cursor.execute("SHOW COLUMNS FROM loans_loan LIKE 'payment_amount'")
        if not cursor.fetchone():
            print("✅ Adding payment_amount to Loan...")
            cursor.execute("""
                ALTER TABLE loans_loan 
                ADD COLUMN payment_amount DECIMAL(10,2) DEFAULT NULL AFTER monthly_payment
            """)
        else:
            print("ℹ️  payment_amount already exists in Loan")
    
    print("\n" + "="*60)
    print("✅ Database updated successfully!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Update LoanType records with repayment frequency")
    print("2. Run: python setup_daily_weekly_loans.py")
    print("3. Test loan application with new fields")
    print()

if __name__ == "__main__":
    try:
        add_repayment_frequency_fields()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
