#!/usr/bin/env python
"""
Script to set up Palm Cash loan types
Run this to configure the loan products
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanType
from decimal import Decimal

def setup_loan_types():
    """Create or update Palm Cash loan types"""
    
    print("🌴 Setting up Palm Cash Loan Types...\n")
    
    # Daily Loan
    daily_loan, created = LoanType.objects.update_or_create(
        name='Daily Loan',
        defaults={
            'description': 'Short-term daily loan with flexible repayment. Perfect for immediate cash needs with daily repayment schedule.',
            'interest_rate': Decimal('45.00'),  # 45% annual interest
            'min_amount': Decimal('2000.00'),   # Minimum K2,000
            'max_amount': Decimal('50000.00'),  # Maximum K50,000
            'min_term_months': 1,               # Minimum 1 month (30 days)
            'max_term_months': 3,               # Maximum 3 months (90 days)
            'is_active': True
        }
    )
    
    if created:
        print("✅ Created 'Daily Loan' type")
    else:
        print("✅ Updated 'Daily Loan' type")
    
    print(f"   - Interest Rate: {daily_loan.interest_rate}% per annum")
    print(f"   - Amount Range: K{daily_loan.min_amount:,.0f} - K{daily_loan.max_amount:,.0f}")
    print(f"   - Term Range: {daily_loan.min_term_months} - {daily_loan.max_term_months} months")
    print()
    
    # Weekly Loan
    weekly_loan, created = LoanType.objects.update_or_create(
        name='Weekly Loan',
        defaults={
            'description': 'Short-term weekly loan with convenient weekly repayment schedule. Ideal for small business owners and entrepreneurs.',
            'interest_rate': Decimal('45.00'),  # 45% annual interest
            'min_amount': Decimal('2000.00'),   # Minimum K2,000
            'max_amount': Decimal('100000.00'), # Maximum K100,000
            'min_term_months': 1,               # Minimum 1 month (4 weeks)
            'max_term_months': 6,               # Maximum 6 months (24 weeks)
            'is_active': True
        }
    )
    
    if created:
        print("✅ Created 'Weekly Loan' type")
    else:
        print("✅ Updated 'Weekly Loan' type")
    
    print(f"   - Interest Rate: {weekly_loan.interest_rate}% per annum")
    print(f"   - Amount Range: K{weekly_loan.min_amount:,.0f} - K{weekly_loan.max_amount:,.0f}")
    print(f"   - Term Range: {weekly_loan.min_term_months} - {weekly_loan.max_term_months} months")
    print()
    
    # Deactivate any other loan types
    other_loans = LoanType.objects.exclude(name__in=['Daily Loan', 'Weekly Loan'])
    if other_loans.exists():
        count = other_loans.update(is_active=False)
        print(f"ℹ️  Deactivated {count} other loan type(s)")
        print()
    
    print("=" * 60)
    print("✅ Loan types setup complete!")
    print("=" * 60)
    print()
    print("📋 Summary:")
    print(f"   Total Active Loan Types: {LoanType.objects.filter(is_active=True).count()}")
    print()
    print("💡 Note:")
    print("   - Both loan types have 45% annual interest rate")
    print("   - Minimum loan amount is K2,000")
    print("   - Daily loans: Best for very short-term needs (1-3 months)")
    print("   - Weekly loans: Better for slightly longer terms (1-6 months)")
    print()
    print("🔗 Next steps:")
    print("   1. Visit http://localhost:8000/admin/loans/loantype/ to view")
    print("   2. Borrowers can now apply for these loan types")
    print("   3. Adjust amounts and terms as needed in the admin panel")
    print()

if __name__ == "__main__":
    try:
        setup_loan_types()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
