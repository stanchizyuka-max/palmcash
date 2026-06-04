#!/usr/bin/env python
"""
Check if branches are doing daily loans vs weekly loans
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from clients.models import Branch
from loans.models import Loan
from payments.models import Payment
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime

def check_loan_types():
    """Check what type of loans each branch is processing"""
    
    print("=" * 80)
    print("     LOAN TYPE ANALYSIS - Daily vs Weekly Operations")
    print("=" * 80)
    print()
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    june_start = timezone.make_aware(datetime(2026, 6, 1, 0, 0, 0))
    today = timezone.now()
    
    for branch in branches:
        print(f"\n{'━' * 80}")
        print(f"  {branch.name.upper()}")
        print(f"{'━' * 80}")
        
        # Get loans for this branch in June
        from accounts.models import User
        
        # Get officers in this branch
        officers = User.objects.filter(
            role='loan_officer',
            officer_assignment__branch__iexact=branch.name,
            is_active=True
        ).distinct()
        
        # Get loans for these officers
        loans_query = Q(loan_officer__in=officers) | Q(borrower__group_memberships__group__assigned_officer__in=officers)
        june_loans = Loan.objects.filter(loans_query).filter(
            disbursement_date__gte=june_start,
            disbursement_date__lte=today
        ).distinct()
        
        # Count by loan type
        daily_loans = june_loans.filter(loan_type='daily').count()
        weekly_loans = june_loans.filter(loan_type='weekly').count()
        monthly_loans = june_loans.filter(loan_type='monthly').count()
        total_loans = june_loans.count()
        
        print(f"\n  📊 LOANS DISBURSED IN JUNE:")
        print(f"    Daily Loans:   {daily_loans}")
        print(f"    Weekly Loans:  {weekly_loans}")
        print(f"    Monthly Loans: {monthly_loans}")
        print(f"    Total:         {total_loans}")
        
        if total_loans > 0:
            daily_pct = (daily_loans / total_loans) * 100
            weekly_pct = (weekly_loans / total_loans) * 100
            monthly_pct = (monthly_loans / total_loans) * 100
            
            print(f"\n  📈 PERCENTAGE:")
            print(f"    Daily:   {daily_pct:.1f}%")
            print(f"    Weekly:  {weekly_pct:.1f}%")
            print(f"    Monthly: {monthly_pct:.1f}%")
        
        # Check payments
        june_payments = Payment.objects.filter(
            loan__in=june_loans,
            payment_date__gte=june_start,
            payment_date__lte=today
        )
        
        payment_count = june_payments.count()
        print(f"\n  💰 PAYMENTS RECEIVED IN JUNE:")
        print(f"    Total Payments: {payment_count}")
        
        # Conclusion
        print(f"\n  💡 CONCLUSION:")
        if daily_loans == 0 and weekly_loans > 0:
            print(f"    ✅ Branch operates WEEKLY LOANS ONLY")
            print(f"    ✅ Daily Vault at K0 is NORMAL - no daily operations needed")
        elif daily_loans > 0 and weekly_loans == 0:
            print(f"    ⚠️  Branch operates DAILY LOANS ONLY")
            print(f"    ⚠️  Transactions should go to Daily Vault, not Weekly!")
        elif daily_loans > 0 and weekly_loans > 0:
            print(f"    ⚠️  Branch operates BOTH daily and weekly loans")
            print(f"    ⚠️  Transactions should be split between vaults")
        elif total_loans == 0:
            print(f"    ℹ️  No loans disbursed in June yet")
        
    print(f"\n{'=' * 80}")
    print()
    print("OVERALL SUMMARY:")
    print("----------------")
    print()
    
    # Overall stats
    all_officers = User.objects.filter(role='loan_officer', is_active=True)
    all_loans_query = Q(loan_officer__in=all_officers) | Q(borrower__group_memberships__group__assigned_officer__in=all_officers)
    all_june_loans = Loan.objects.filter(all_loans_query).filter(
        disbursement_date__gte=june_start,
        disbursement_date__lte=today
    ).distinct()
    
    total_daily = all_june_loans.filter(loan_type='daily').count()
    total_weekly = all_june_loans.filter(loan_type='weekly').count()
    total_monthly = all_june_loans.filter(loan_type='monthly').count()
    grand_total = all_june_loans.count()
    
    print(f"Across ALL branches in June:")
    print(f"  Daily Loans:   {total_daily}")
    print(f"  Weekly Loans:  {total_weekly}")
    print(f"  Monthly Loans: {total_monthly}")
    print(f"  Total:         {grand_total}")
    print()
    
    if total_daily == 0:
        print("✅ NO DAILY LOANS being processed system-wide")
        print("✅ Daily Vaults at K0 is EXPECTED and CORRECT")
        print("💡 All branches are operating weekly loans only")
    elif total_weekly == 0:
        print("⚠️  ONLY DAILY LOANS being processed")
        print("⚠️  All transactions should go to Daily Vault")
        print("🔧 Need to configure loan processing to use Daily Vault")
    else:
        print("⚠️  BOTH daily and weekly loans are being processed")
        print("⚠️  Transactions should be routed based on loan type")
        print("🔧 Need to ensure loan payments go to correct vault")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    check_loan_types()
