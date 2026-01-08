#!/usr/bin/env python
"""
Debug script to check security deposits status
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

print("=== SECURITY DEPOSITS DEBUG ===")

from loans.models import SecurityDeposit

# Check all security deposits
all_deposits = SecurityDeposit.objects.all()
print(f"Total Security Deposits: {all_deposits.count()}")

print("\n=== ALL DEPOSITS ===")
for deposit in all_deposits:
    print(f"Loan #{deposit.loan.application_number if deposit.loan else 'N/A'}")
    print(f"  Borrower: {deposit.loan.borrower.get_full_name() if deposit.loan else 'N/A'}")
    print(f"  Required: K{deposit.required_amount}")
    print(f"  Paid: K{deposit.paid_amount}")
    print(f"  Payment Date: {deposit.payment_date}")
    print(f"  Verification Date: {deposit.verification_date}")
    print(f"  Is Verified: {deposit.is_verified}")
    print(f"  Verified By: {deposit.verified_by.username if deposit.verified_by else 'N/A'}")
    print(f"  Status: {'Verified' if deposit.is_verified else 'Not Verified'}")
    print("---")

# Check verified deposits only
verified_deposits = SecurityDeposit.objects.filter(is_verified=True)
print(f"\n=== VERIFIED DEPOSITS ===")
print(f"Verified Deposits Count: {verified_deposits.count()}")

for deposit in verified_deposits:
    print(f"Loan #{deposit.loan.application_number if deposit.loan else 'N/A'} - K{deposit.paid_amount}")

# Check deposits with paid_amount > 0
paid_deposits = SecurityDeposit.objects.filter(paid_amount__gt=0)
print(f"\n=== PAID DEPOSITS ===")
print(f"Paid Deposits Count: {paid_deposits.count()}")

for deposit in paid_deposits:
    print(f"Loan #{deposit.loan.application_number if deposit.loan else 'N/A'} - K{deposit.paid_amount} - Verified: {deposit.is_verified}")

print("\n=== END DEBUG ===")
