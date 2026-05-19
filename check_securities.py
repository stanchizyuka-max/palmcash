#!/usr/bin/env python
"""
Check securities data in the system
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from loans.models import Loan, SecurityDeposit, SecurityTopUpRequest, SecurityTransaction
from django.db.models import Sum, Count

print("=" * 70)
print("CHECKING SECURITIES DATA")
print("=" * 70)
print()

# Check SecurityDeposit
print("1. Security Deposits:")
total_deposits = SecurityDeposit.objects.count()
verified_deposits = SecurityDeposit.objects.filter(is_verified=True).count()
unverified_deposits = SecurityDeposit.objects.filter(is_verified=False).count()

print(f"   Total deposits: {total_deposits}")
print(f"   Verified: {verified_deposits}")
print(f"   Unverified: {unverified_deposits}")

if total_deposits > 0:
    print("\n   Sample deposits:")
    for deposit in SecurityDeposit.objects.all()[:5]:
        print(f"   - Loan: {deposit.loan.application_number}, Amount: K{deposit.paid_amount}, Verified: {deposit.is_verified}")
print()

# Check SecurityTopUpRequest
print("2. Security Top-Ups:")
total_topups = SecurityTopUpRequest.objects.count()
approved_topups = SecurityTopUpRequest.objects.filter(status='approved').count()

print(f"   Total top-ups: {total_topups}")
print(f"   Approved: {approved_topups}")

if total_topups > 0:
    print("\n   Sample top-ups:")
    for topup in SecurityTopUpRequest.objects.all()[:5]:
        print(f"   - Loan: {topup.loan.application_number}, Amount: K{topup.requested_amount}, Status: {topup.status}")
print()

# Check SecurityTransaction
print("3. Security Transactions:")
total_transactions = SecurityTransaction.objects.count()
approved_transactions = SecurityTransaction.objects.filter(status='approved').count()

print(f"   Total transactions: {total_transactions}")
print(f"   Approved: {approved_transactions}")

if total_transactions > 0:
    print("\n   Transactions by type:")
    for tx_type in ['adjustment', 'return', 'carry_forward', 'withdrawal']:
        count = SecurityTransaction.objects.filter(transaction_type=tx_type, status='approved').count()
        total_amount = SecurityTransaction.objects.filter(
            transaction_type=tx_type, 
            status='approved'
        ).aggregate(total=Sum('amount'))['total'] or 0
        print(f"   - {tx_type}: {count} transactions, Total: K{total_amount}")
print()

# Check loans with securities
print("4. Loans with Securities:")
loans_with_deposits = Loan.objects.filter(securitydeposit__isnull=False).distinct().count()
total_loans = Loan.objects.count()

print(f"   Total loans: {total_loans}")
print(f"   Loans with deposits: {loans_with_deposits}")
print()

# Calculate total securities
print("5. Total Securities Calculation:")
upfront = SecurityDeposit.objects.filter(is_verified=True).aggregate(total=Sum('paid_amount'))['total'] or 0
topups = SecurityTopUpRequest.objects.filter(status='approved').aggregate(total=Sum('requested_amount'))['total'] or 0
adjustments = SecurityTransaction.objects.filter(status='approved', transaction_type='adjustment').aggregate(total=Sum('amount'))['total'] or 0
returned = SecurityTransaction.objects.filter(status='approved', transaction_type='return').aggregate(total=Sum('amount'))['total'] or 0
carry_forwards = SecurityTransaction.objects.filter(status='approved', transaction_type='carry_forward').aggregate(total=Sum('amount'))['total'] or 0
withdrawals = SecurityTransaction.objects.filter(status='approved', transaction_type='withdrawal').aggregate(total=Sum('amount'))['total'] or 0

balance = (upfront + topups + carry_forwards) - (adjustments + returned + withdrawals)

print(f"   Upfront deposits (verified): K{upfront}")
print(f"   Top-ups (approved): K{topups}")
print(f"   Carry forwards: K{carry_forwards}")
print(f"   Adjustments: K{adjustments}")
print(f"   Returned: K{returned}")
print(f"   Withdrawals: K{withdrawals}")
print(f"   BALANCE: K{balance}")
print()

# Check if there are any unverified deposits that should be verified
if unverified_deposits > 0:
    print("⚠️  WARNING: There are unverified security deposits!")
    print("   These deposits are not included in the balance calculation.")
    print("   Unverified deposits:")
    for deposit in SecurityDeposit.objects.filter(is_verified=False)[:10]:
        print(f"   - Loan: {deposit.loan.application_number}, Amount: K{deposit.paid_amount}, Date: {deposit.created_at}")
    print()

print("=" * 70)
print("DIAGNOSIS:")
print("=" * 70)

if total_deposits == 0:
    print("❌ No security deposits found in the system")
    print("   Solution: Security deposits need to be recorded when loans are created")
elif verified_deposits == 0:
    print("❌ No verified security deposits found")
    print("   Solution: Existing deposits need to be verified by managers")
elif balance == 0:
    print("⚠️  Balance is K0.00 but deposits exist")
    print("   This could mean all securities have been returned/adjusted")
else:
    print(f"✅ Securities system is working. Total balance: K{balance}")

print("=" * 70)
