"""
Setup script for Daily and Weekly loan types at 45% interest
Run this to configure the system for daily/weekly lending

Usage: python setup_daily_weekly_loan_types.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import LoanType
from decimal import Decimal


def setup_loan_types():
    """Create daily and weekly loan types"""
    
    loan_types = [
        {
            'name': 'Daily Loan - Short Term',
            'description': 'Quick cash loan with daily repayments. Perfect for urgent needs.',
            'interest_rate': Decimal('45.00'),
            'min_amount': Decimal('500.00'),
            'max_amount': Decimal('5000.00'),
            'repayment_frequency': 'daily',
            'min_term_days': 7,
            'max_term_days': 30,
            'is_active': True
        },
        {
            'name': 'Daily Loan - Medium Term',
            'description': 'Flexible daily repayment loan for medium-term needs.',
            'interest_rate': Decimal('45.00'),
            'min_amount': Decimal('1000.00'),
            'max_amount': Decimal('10000.00'),
            'repayment_frequency': 'daily',
            'min_term_days': 30,
            'max_term_days': 90,
            'is_active': True
        },
        {
            'name': 'Weekly Loan - Short Term',
            'description': 'Convenient weekly repayment loan for short-term financing.',
            'interest_rate': Decimal('45.00'),
            'min_amount': Decimal('1000.00'),
            'max_amount': Decimal('10000.00'),
            'repayment_frequency': 'weekly',
            'min_term_weeks': 4,
            'max_term_weeks': 12,
            'is_active': True
        },
        {
            'name': 'Weekly Loan - Medium Term',
            'description': 'Extended weekly repayment loan for larger amounts.',
            'interest_rate': Decimal('45.00'),
            'min_amount': Decimal('5000.00'),
            'max_amount': Decimal('50000.00'),
            'repayment_frequency': 'weekly',
            'min_term_weeks': 12,
            'max_term_weeks': 26,
            'is_active': True
        },
        {
            'name': 'Weekly Loan - Long Term',
            'description': 'Long-term weekly repayment loan for substantial financing needs.',
            'interest_rate': Decimal('45.00'),
            'min_amount': Decimal('10000.00'),
            'max_amount': Decimal('100000.00'),
            'repayment_frequency': 'weekly',
            'min_term_weeks': 26,
            'max_term_weeks': 52,
            'is_active': True
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    print("Setting up Daily and Weekly loan types...")
    print("="*60)
    
    for loan_type_data in loan_types:
        loan_type, created = LoanType.objects.update_or_create(
            name=loan_type_data['name'],
            defaults=loan_type_data
        )
        
        if created:
            created_count += 1
            print(f"✓ Created: {loan_type.name}")
            print(f"  - Frequency: {loan_type.get_repayment_frequency_display()}")
            print(f"  - Interest Rate: {loan_type.interest_rate}%")
            print(f"  - Amount Range: K{loan_type.min_amount:,.2f} - K{loan_type.max_amount:,.2f}")
            if loan_type.repayment_frequency == 'daily':
                print(f"  - Term Range: {loan_type.min_term_days}-{loan_type.max_term_days} days")
            else:
                print(f"  - Term Range: {loan_type.min_term_weeks}-{loan_type.max_term_weeks} weeks")
        else:
            updated_count += 1
            print(f"↻ Updated: {loan_type.name}")
        
        print()
    
    # Deactivate old monthly loan types
    monthly_loans = LoanType.objects.filter(
        repayment_frequency__isnull=True
    ) | LoanType.objects.exclude(
        repayment_frequency__in=['daily', 'weekly']
    )
    
    deactivated = monthly_loans.update(is_active=False)
    if deactivated:
        print(f"⚠️  Deactivated {deactivated} old monthly loan type(s)")
        print()
    
    print("="*60)
    print(f"Summary:")
    print(f"  Created: {created_count} loan types")
    print(f"  Updated: {updated_count} loan types")
    print(f"  Deactivated: {deactivated} old loan types")
    print(f"  Total Active: {LoanType.objects.filter(is_active=True).count()} loan types")
    print("="*60)
    print("\n✓ Daily and Weekly loan types setup complete!")
    print("\nSystem Configuration:")
    print("  - Interest Rate: 45% (flat rate)")
    print("  - Repayment Frequencies: Daily and Weekly only")
    print("  - No monthly loans")
    print("\nNext steps:")
    print("1. Review loan types at: /loans/manage/loan-types/")
    print("2. Borrowers can now apply for daily or weekly loans")
    print("3. System will calculate payments based on frequency")


if __name__ == '__main__':
    setup_loan_types()
