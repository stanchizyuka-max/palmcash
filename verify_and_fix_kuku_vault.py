#!/usr/bin/env python
"""
Verify and fix KUKU branch vault balance after retroactive transaction creation
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

# Django imports (must come after django.setup())
from django.db.models import Sum, Q
from django.db import transaction
from decimal import Decimal

# App imports
from expenses.models import VaultTransaction, WeeklyVault, DailyVault
from clients.models import Branch

print("\n" + "="*70)
print("VERIFY AND FIX KUKU BRANCH VAULT BALANCE")
print("="*70)

# Get KUKU branch
branch = Branch.objects.filter(name__iexact='KUKU').first()
if not branch:
    print("\n❌ KUKU branch not found!")
    exit()

print(f"\n✅ Found branch: {branch.name}")

# Get vault records
daily_vault = DailyVault.objects.filter(branch=branch).first()
weekly_vault = WeeklyVault.objects.filter(branch=branch).first()

print(f"\n📊 CURRENT VAULT RECORDS:")
if daily_vault:
    print(f"Daily Vault Balance:   K{daily_vault.balance}")
else:
    print(f"Daily Vault Balance:   NOT FOUND")

if weekly_vault:
    print(f"Weekly Vault Balance:  K{weekly_vault.balance}")
else:
    print(f"Weekly Vault Balance:  NOT FOUND")

total_stored = Decimal('0.00')
if daily_vault:
    total_stored += daily_vault.balance
if weekly_vault:
    total_stored += weekly_vault.balance

print(f"Total Balance:         K{total_stored}")

# Calculate from transactions
print(f"\n🔍 CALCULATING FROM TRANSACTIONS...")

def calculate_vault_balance(branch_name, vault_type):
    """Calculate vault balance from all transactions"""
    transactions = VaultTransaction.objects.filter(
        branch__iexact=branch_name,
        vault_type=vault_type,
        is_reversed=False
    ).order_by('transaction_date', 'id')
    
    total_in = Decimal('0.00')
    total_out = Decimal('0.00')
    
    print(f"\n{vault_type.upper()} Vault:")
    print(f"  Total transactions: {transactions.count()}")
    
    for tx in transactions:
        if tx.direction == 'in':
            total_in += tx.amount
        else:
            total_out += tx.amount
    
    print(f"  Total IN:  K{total_in}")
    print(f"  Total OUT: K{total_out}")
    
    calculated = total_in - total_out
    print(f"  Calculated Balance: K{calculated}")
    
    return calculated, total_in, total_out

daily_calculated, daily_in, daily_out = calculate_vault_balance(branch.name, 'daily')
weekly_calculated, weekly_in, weekly_out = calculate_vault_balance(branch.name, 'weekly')

total_calculated = daily_calculated + weekly_calculated

print(f"\n📊 COMPARISON:")
print(f"{'='*70}")
print(f"Daily Vault:")
if daily_vault:
    print(f"  Stored Balance:     K{daily_vault.balance}")
    print(f"  Calculated Balance: K{daily_calculated}")
    daily_diff = daily_vault.balance - daily_calculated
    print(f"  Difference:         K{daily_diff}")
    if daily_diff == 0:
        print(f"  ✅ Daily vault balance is CORRECT")
    else:
        print(f"  ❌ Daily vault balance is INCORRECT")
else:
    print(f"  ❌ Daily vault record not found")

print(f"\nWeekly Vault:")
if weekly_vault:
    print(f"  Stored Balance:     K{weekly_vault.balance}")
    print(f"  Calculated Balance: K{weekly_calculated}")
    weekly_diff = weekly_vault.balance - weekly_calculated
    print(f"  Difference:         K{weekly_diff}")
    if weekly_diff == 0:
        print(f"  ✅ Weekly vault balance is CORRECT")
    else:
        print(f"  ❌ Weekly vault balance is INCORRECT")
else:
    print(f"  ❌ Weekly vault record not found")

print(f"\n📊 TOTAL:")
print(f"  Stored Total:     K{total_stored}")
print(f"  Calculated Total: K{total_calculated}")
total_diff = total_stored - total_calculated
print(f"  Difference:       K{total_diff}")

# Check for the retroactive transactions
print(f"\n🔍 CHECKING RETROACTIVE TRANSACTIONS...")
retro_txs = VaultTransaction.objects.filter(
    branch__iexact=branch.name,
    reference_number__startswith='RETRO-DISB'
).order_by('id')

if retro_txs.exists():
    print(f"\n✅ Found {retro_txs.count()} retroactive transaction(s):")
    for tx in retro_txs:
        print(f"\n  ID: {tx.id}")
        print(f"  Loan: {tx.loan.application_number if tx.loan else 'N/A'}")
        print(f"  Borrower: {tx.loan.borrower.get_full_name() if tx.loan else 'N/A'}")
        print(f"  Amount: K{tx.amount}")
        print(f"  Balance After: K{tx.balance_after}")
        print(f"  Date: {tx.transaction_date}")
else:
    print(f"\n⚠️  No retroactive transactions found")

# Determine if fix is needed
needs_fix = False
if daily_vault and daily_diff != 0:
    needs_fix = True
if weekly_vault and weekly_diff != 0:
    needs_fix = True

if not needs_fix:
    print(f"\n{'='*70}")
    print(f"✅ ALL BALANCES ARE CORRECT!")
    print(f"{'='*70}")
    exit()

# Offer to fix
print(f"\n{'='*70}")
print(f"FIX REQUIRED")
print(f"{'='*70}")

print(f"\nThe vault balances need to be corrected:")
if daily_vault and daily_diff != 0:
    print(f"  Daily Vault: K{daily_vault.balance} → K{daily_calculated} (adjust by K{-daily_diff})")
if weekly_vault and weekly_diff != 0:
    print(f"  Weekly Vault: K{weekly_vault.balance} → K{weekly_calculated} (adjust by K{-weekly_diff})")

response = input("\nFix vault balances? (yes/no): ")
if response.lower() != 'yes':
    print("\n❌ Aborted. No changes made.")
    exit()

# Fix the balances
print(f"\n🔄 Updating vault balances...")

with transaction.atomic():
    if daily_vault and daily_diff != 0:
        old_balance = daily_vault.balance
        daily_vault.balance = daily_calculated
        daily_vault.save()
        print(f"  ✅ Updated Daily Vault: K{old_balance} → K{daily_calculated}")
    
    if weekly_vault and weekly_diff != 0:
        old_balance = weekly_vault.balance
        weekly_vault.balance = weekly_calculated
        weekly_vault.save()
        print(f"  ✅ Updated Weekly Vault: K{old_balance} → K{weekly_calculated}")

print(f"\n{'='*70}")
print(f"DONE")
print(f"{'='*70}")

print(f"\n✅ Vault balances have been corrected!")
print(f"\n💡 NEXT STEPS:")
print(f"1. Check the KUKU branch vault dashboard")
print(f"2. Verify the balances match the calculated amounts")
print(f"3. Check the transaction history")

print(f"\n{'='*70}\n")
