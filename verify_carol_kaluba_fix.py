#!/usr/bin/env python
"""
Verify that Carol and Kaluba's loans are properly fixed with correct vault balances
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

# Django imports (must come after django.setup())
from django.db.models import Q, Sum
from decimal import Decimal

# App imports
from loans.models import Loan, WeeklyVault
from expenses.models import VaultTransaction
from accounts.models import User
from clients.models import Branch

print("\n" + "="*70)
print("VERIFY CAROL AND KALUBA LOAN FIX")
print("="*70)

# Find Carol and Kaluba
carol = User.objects.filter(
    Q(first_name__icontains='carol') & Q(last_name__icontains='bwalya'),
    role='borrower'
).first()

kaluba = User.objects.filter(
    Q(first_name__icontains='kaluba') & Q(last_name__icontains='bwalya'),
    role='borrower'
).first()

if not carol or not kaluba:
    print("\n❌ Could not find Carol or Kaluba")
    exit()

print(f"\n✅ Found borrowers:")
print(f"   Carol: {carol.get_full_name()} (ID: {carol.id})")
print(f"   Kaluba: {kaluba.get_full_name()} (ID: {kaluba.id})")

# Get their loans
carol_loan = Loan.objects.filter(borrower=carol, status='active').first()
kaluba_loan = Loan.objects.filter(borrower=kaluba, status='active').first()

if not carol_loan or not kaluba_loan:
    print("\n❌ Could not find active loans")
    exit()

print(f"\n📋 LOANS:")
print(f"   Carol:  {carol_loan.application_number} - K{carol_loan.principal_amount}")
print(f"   Kaluba: {kaluba_loan.application_number} - K{kaluba_loan.principal_amount}")

# Check vault transactions
print(f"\n🔍 CHECKING VAULT TRANSACTIONS...")

carol_tx = VaultTransaction.objects.filter(
    loan=carol_loan,
    transaction_type='loan_disbursement',
    direction='out'
).first()

kaluba_tx = VaultTransaction.objects.filter(
    loan=kaluba_loan,
    transaction_type='loan_disbursement',
    direction='out'
).first()

if carol_tx:
    print(f"   ✅ Carol vault transaction exists (ID: {carol_tx.id})")
    print(f"      Date: {carol_tx.transaction_date}")
    print(f"      Amount: K{carol_tx.amount}")
    print(f"      Balance after: K{carol_tx.balance_after}")
else:
    print(f"   ❌ Carol vault transaction MISSING")

if kaluba_tx:
    print(f"   ✅ Kaluba vault transaction exists (ID: {kaluba_tx.id})")
    print(f"      Date: {kaluba_tx.transaction_date}")
    print(f"      Amount: K{kaluba_tx.amount}")
    print(f"      Balance after: K{kaluba_tx.balance_after}")
else:
    print(f"   ❌ Kaluba vault transaction MISSING")

# Check KUKU vault balance
print(f"\n💰 CHECKING KUKU VAULT BALANCE...")

branch = Branch.objects.filter(name__iexact='KUKU').first()
if not branch:
    print("   ❌ KUKU branch not found")
    exit()

weekly_vault = WeeklyVault.objects.filter(branch=branch).first()
if not weekly_vault:
    print("   ❌ Weekly vault not found")
    exit()

print(f"   Current stored balance: K{weekly_vault.balance}")

# Calculate from transactions
transactions = VaultTransaction.objects.filter(
    branch__iexact='KUKU',
    vault_type='weekly'
).order_by('transaction_date', 'id')

total_in = Decimal('0.00')
total_out = Decimal('0.00')

for tx in transactions:
    if tx.direction == 'in':
        total_in += tx.amount
    else:
        total_out += tx.amount

calculated_balance = total_in - total_out

print(f"   Calculated from transactions: K{calculated_balance}")
print(f"   Difference: K{weekly_vault.balance - calculated_balance}")

if weekly_vault.balance == calculated_balance:
    print(f"   ✅ Balance is CORRECT")
else:
    print(f"   ❌ Balance MISMATCH")

# Check if Carol and Kaluba transactions are included
print(f"\n🔍 VERIFYING CAROL AND KALUBA IN TRANSACTION HISTORY...")

carol_in_history = VaultTransaction.objects.filter(
    branch__iexact='KUKU',
    vault_type='weekly',
    loan=carol_loan
).exists()

kaluba_in_history = VaultTransaction.objects.filter(
    branch__iexact='KUKU',
    vault_type='weekly',
    loan=kaluba_loan
).exists()

if carol_in_history:
    print(f"   ✅ Carol's loan is in vault transaction history")
else:
    print(f"   ❌ Carol's loan NOT in vault transaction history")

if kaluba_in_history:
    print(f"   ✅ Kaluba's loan is in vault transaction history")
else:
    print(f"   ❌ Kaluba's loan NOT in vault transaction history")

# Summary
print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")

all_good = (
    carol_tx is not None and
    kaluba_tx is not None and
    weekly_vault.balance == calculated_balance and
    carol_in_history and
    kaluba_in_history
)

if all_good:
    print(f"\n✅ ALL CHECKS PASSED!")
    print(f"   - Both loans have vault transactions")
    print(f"   - Vault balance is correct")
    print(f"   - Both loans appear in transaction history")
    print(f"\n🎉 The fix was successful!")
else:
    print(f"\n⚠️  SOME ISSUES FOUND:")
    if not carol_tx:
        print(f"   - Carol's vault transaction is missing")
    if not kaluba_tx:
        print(f"   - Kaluba's vault transaction is missing")
    if weekly_vault.balance != calculated_balance:
        print(f"   - Vault balance doesn't match calculated balance")
    if not carol_in_history:
        print(f"   - Carol's loan not in transaction history")
    if not kaluba_in_history:
        print(f"   - Kaluba's loan not in transaction history")

print(f"\n{'='*70}\n")
