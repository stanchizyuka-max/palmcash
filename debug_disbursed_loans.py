#!/usr/bin/env python
"""
Debug script to check disbursed loans in the database
Run this on PythonAnywhere to investigate the disbursed amount issue
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/username/palmcash')  # Replace 'username' with your actual username
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')

# Setup Django
django.setup()

from loans.models import Loan
from django.db.models import Sum
from accounts.models import User

def debug_disbursed_loans():
    print("=" * 60)
    print("DEBUGGING DISBURSED LOANS ISSUE")
    print("=" * 60)
    
    # Check all loans in system
    all_loans = Loan.objects.all()
    print(f"\n1. TOTAL LOANS IN SYSTEM: {all_loans.count()}")
    
    # Check loans by status
    print("\n2. LOANS BY STATUS:")
    statuses = all_loans.values_list('status', flat=True).distinct()
    for status in statuses:
        count = all_loans.filter(status=status).count()
        amount = all_loans.filter(status=status).aggregate(total=Sum('principal_amount'))['total'] or 0
        print(f"   {status}: {count} loans, Total amount: K{amount}")
    
    # Check specifically for disbursed loans
    print("\n3. DISBURSED LOANS:")
    disbursed_loans = all_loans.filter(status='disbursed')
    print(f"   Count: {disbursed_loans.count()}")
    
    if disbursed_loans.exists():
        print("   Disbursed loan details:")
        for loan in disbursed_loans[:10]:  # Show first 10
            print(f"     - ID: {loan.id}, Amount: K{loan.principal_amount}, Borrower: {loan.borrower.get_full_name()}")
    else:
        print("   No disbursed loans found!")
    
    # Check active and completed loans
    print("\n4. ACTIVE LOANS:")
    active_loans = all_loans.filter(status='active')
    print(f"   Count: {active_loans.count()}")
    active_amount = active_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
    print(f"   Total amount: K{active_amount}")
    
    print("\n5. COMPLETED LOANS:")
    completed_loans = all_loans.filter(status='completed')
    print(f"   Count: {completed_loans.count()}")
    completed_amount = completed_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
    print(f"   Total amount: K{completed_amount}")
    
    # Calculate what should be shown as disbursed
    total_disbursed_amount = all_loans.filter(
        status__in=['active', 'completed', 'disbursed']
    ).aggregate(total=Sum('principal_amount'))['total'] or 0
    
    print(f"\n6. EXPECTED DISBURSED AMOUNT: K{total_disbursed_amount}")
    print(f"   (Active: K{active_amount} + Completed: K{completed_amount} + Disbursed: K{disbursed_loans.aggregate(total=Sum('principal_amount'))['total'] or 0})")
    
    # Check if there are any loans with unusual statuses
    print("\n7. ALL LOAN STATUSES IN SYSTEM:")
    all_statuses = all_loans.values_list('status', flat=True).distinct()
    for status in sorted(all_statuses):
        count = all_loans.filter(status=status).count()
        print(f"   '{status}': {count} loans")
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    debug_disbursed_loans()
