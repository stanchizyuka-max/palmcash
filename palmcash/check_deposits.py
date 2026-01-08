#!/usr/bin/env python
import os
import sys
import django

# Add the project path
sys.path.append('c:/Users/Doreen/OneDrive/Desktop/palm cash/palmcash/palmcash')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')

# Setup Django
django.setup()

from loans.models import SecurityDeposit, Loan
from django.db.models import Sum, Count

print("=== SECURITY DEPOSIT ANALYSIS ===")
print()

# Check ALL security deposits
all_deposits = SecurityDeposit.objects.all()
print(f"1. ALL security deposits: {all_deposits.count()}")

for deposit in all_deposits:
    print(f"   ID {deposit.id}: Loan {deposit.loan.application_number if deposit.loan else 'None'}")
    print(f"      Required: K{deposit.required_amount}")
    print(f"      Paid: K{deposit.paid_amount}")
    print(f"      Is Verified: {deposit.is_verified}")
    print(f"      Payment Date: {deposit.payment_date}")
    print()

# Check PENDING deposits (paid > 0, not verified)
pending_deposits = SecurityDeposit.objects.filter(
    paid_amount__gt=0,
    is_verified=False
)
print(f"2. PENDING deposits (paid > 0, not verified): {pending_deposits.count()}")

for deposit in pending_deposits:
    print(f"   ID {deposit.id}: Loan {deposit.loan.application_number if deposit.loan else 'None'}")
    print(f"      Required: K{deposit.required_amount}")
    print(f"      Paid: K{deposit.paid_amount}")
    print(f"      Is Verified: {deposit.is_verified}")
    print()

# Check deposits with paid_amount = 0
zero_paid = SecurityDeposit.objects.filter(paid_amount=0)
print(f"3. Deposits with paid_amount = 0: {zero_paid.count()}")

# Check deposits that are verified
verified_deposits = SecurityDeposit.objects.filter(is_verified=True)
print(f"4. VERIFIED deposits: {verified_deposits.count()}")

# Check loans without security deposits
loans_without_deposits = Loan.objects.filter(securitydeposit__isnull=True)
print(f"5. Loans without security deposits: {loans_without_deposits.count()}")

# Check for the specific loan LA-81A75673
try:
    specific_loan = Loan.objects.get(application_number='LA-81A75673')
    if hasattr(specific_loan, 'securitydeposit'):
        if specific_loan.securitydeposit:
            print(f"6. SPECIFIC LOAN {specific_loan.application_number}:")
            print(f"   Has Security Deposit: YES")
            print(f"   Deposit ID: {specific_loan.securitydeposit.id}")
            print(f"   Required: K{specific_loan.securitydeposit.required_amount}")
            print(f"   Paid: K{specific_loan.securitydeposit.paid_amount}")
            print(f"   Is Verified: {specific_loan.securitydeposit.is_verified}")
        else:
            print(f"6. SPECIFIC LOAN {specific_loan.application_number}: Has Security Deposit: NO (None)")
    else:
        print(f"6. SPECIFIC LOAN {specific_loan.application_number}: Has Security Deposit: NO (no attribute)")
except Loan.DoesNotExist:
    print(f"6. SPECIFIC LOAN LA-81A75673: NOT FOUND")

print("\n=== END ANALYSIS ===")
