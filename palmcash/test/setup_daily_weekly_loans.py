#!/usr/bin/env python
"""
Configure Daily and Weekly loan types for Palm Cash
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanType
from decimal import Decimal

def setup_daily_weekly_loans():
    """Configure daily and weekly loan products"""
    
    print("🌴 Setting up Daily & Weekly Loans for Palm Cash...\n")
    
    # Daily Loan
    daily_loan, created = LoanType.objects.update_or_create(
        name='Daily Loan',
        defaults={
            'description': 'Short-term daily repayment loan. Pay a small amount every day. Perfect for daily income earners like market vendors and taxi drivers.',
            'interest_rate': Decimal('45.00'),
            'min_amount': Decimal('2000.00'),
            'max_amount': Decimal('50000.00'),
            'min_term_months': 1,
            'max_term_months': 3,
            'min_term_days': 30,
            'max_term_days': 90,
            'min_term_weeks': None,
            'max_term_weeks': None,
            'repayment_frequency': 'daily',
            'is_active': True
        }
    )
    
    print("✅ Daily Loan configured")
    print(f"   - Repayment: DAILY")
    print(f"   - Interest: {daily_loan.interest_rate}% per annum")
    print(f"   - Amount: K{daily_loan.min_amount:,.0f} - K{daily_loan.max_amount:,.0f}")
    print(f"   - Term: {daily_loan.min_term_days} - {daily_loan.max_term_days} days")
    print()
    
    # Weekly Loan
    weekly_loan, created = LoanType.objects.update_or_create(
        name='Weekly Loan',
        defaults={
            'description': 'Flexible weekly repayment loan. Pay once per week. Ideal for small business owners and weekly income earners.',
            'interest_rate': Decimal('45.00'),
            'min_amount': Decimal('2000.00'),
            'max_amount': Decimal('100000.00'),
            'min_term_months': 1,
            'max_term_months': 6,
            'min_term_days': None,
            'max_term_days': None,
            'min_term_weeks': 4,
            'max_term_weeks': 24,
            'repayment_frequency': 'weekly',
            'is_active': True
        }
    )
    
    print("✅ Weekly Loan configured")
    print(f"   - Repayment: WEEKLY")
    print(f"   - Interest: {weekly_loan.interest_rate}% per annum")
    print(f"   - Amount: K{weekly_loan.min_amount:,.0f} - K{weekly_loan.max_amount:,.0f}")
    print(f"   - Term: {weekly_loan.min_term_weeks} - {weekly_loan.max_term_weeks} weeks")
    print()
    
    # Deactivate other loan types
    other_loans = LoanType.objects.exclude(name__in=['Daily Loan', 'Weekly Loan'])
    if other_loans.exists():
        count = other_loans.update(is_active=False)
        print(f"ℹ️  Deactivated {count} other loan type(s)")
        print()
    
    print("="*70)
    print("✅ Palm Cash Daily & Weekly Loan System Ready!")
    print("="*70)
    print()
    print("📊 Loan Products Summary:")
    print()
    print("┌─────────────┬──────────┬─────────────┬──────────────┬──────────┐")
    print("│ Loan Type   │ Frequency│ Min Amount  │ Max Amount   │ Term     │")
    print("├─────────────┼──────────┼─────────────┼──────────────┼──────────┤")
    print(f"│ Daily Loan  │ Daily    │ K{daily_loan.min_amount:>10,.0f} │ K{daily_loan.max_amount:>11,.0f} │ 30-90d   │")
    print(f"│ Weekly Loan │ Weekly   │ K{weekly_loan.min_amount:>10,.0f} │ K{weekly_loan.max_amount:>11,.0f} │ 4-24w    │")
    print("└─────────────┴──────────┴─────────────┴──────────────┴──────────┘")
    print()
    print("💡 Examples:")
    print()
    print("Daily Loan (K10,000 for 60 days):")
    principal = 10000
    days = 60
    rate = 0.45
    interest = principal * rate * (days / 365)
    total = principal + interest
    daily_payment = total / days
    print(f"  - Daily Payment: K{daily_payment:,.2f}")
    print(f"  - Total Interest: K{interest:,.2f}")
    print(f"  - Total Repayment: K{total:,.2f}")
    print()
    
    print("Weekly Loan (K10,000 for 12 weeks):")
    weeks = 12
    interest = principal * rate * (weeks / 52)
    total = principal + interest
    weekly_payment = total / weeks
    print(f"  - Weekly Payment: K{weekly_payment:,.2f}")
    print(f"  - Total Interest: K{interest:,.2f}")
    print(f"  - Total Repayment: K{total:,.2f}")
    print()
    print("🎯 System is ready for borrowers to apply!")
    print()

if __name__ == "__main__":
    try:
        setup_daily_weekly_loans()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
