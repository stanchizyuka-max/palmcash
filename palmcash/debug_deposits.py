#!/usr/bin/env python
import os
import sys
import django

# Add the project path
sys.path.append('c:/Users/Doreen/OneDrive/Desktop/palm cash/palmcash/palmcash')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')

# Setup Django
django.setup()

# Now import and check
from loans.models import SecurityDeposit, Loan
from django.db.models import Sum

print("=== SECURITY DEPOSIT DEBUG ===")
print()

# Check all security deposits
all_deposits = SecurityDeposit.objects.all()
print(f"Total security deposits in database: {all_deposits.count()}")

for deposit in all_deposits:
    print(f"Deposit ID: {deposit.id}")
    print(f"  Loan: {deposit.loan.application_number if deposit.loan else 'No Loan'}")
    print(f"  Borrower: {deposit.loan.borrower.get_full_name() if deposit.loan and deposit.loan.borrower else 'No Borrower'}")
    print(f"  Required: K{deposit.required_amount}")
    print(f"  Paid: K{deposit.paid_amount}")
    print(f"  Is Verified: {deposit.is_verified}")
    print(f"  Payment Date: {deposit.payment_date}")
    print()

# Check pending deposits (paid but not verified)
pending_deposits = SecurityDeposit.objects.filter(
    is_verified=False,
    paid_amount__gt=0
)
print(f"Pending deposits (paid but not verified): {pending_deposits.count()}")

for deposit in pending_deposits:
    print(f"Pending Deposit - Loan: {deposit.loan.application_number if deposit.loan else 'No Loan'}, Paid: K{deposit.paid_amount}, Verified: {deposit.is_verified}")

# Check loans without security deposits
loans_without_deposits = Loan.objects.filter(securitydeposit__isnull=True)
print(f"\nLoans without security deposits: {loans_without_deposits.count()}")

for loan in loans_without_deposits[:5]:  # Show first 5
    print(f"Loan without deposit: {loan.application_number} - Status: {loan.status}")

print("\n=== END DEBUG ===")
