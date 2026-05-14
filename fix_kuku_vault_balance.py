#!/usr/bin/env python
"""
Fix KUKU branch vault balance after adding missing Carol and Kaluba transactions
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
from expenses.models import VaultTransaction, WeeklyVault
from clients.models import Branch

print("\n" + "="*70)
print("FIX KUKU VAULT BALANCE")
print("="*70)

# Get KUKU branch
branch = Branch.objects.filter(name__iexact='KUKU').first()
if not branch:
    print("\n❌ KUKU branch not found!")
    exit()

print(f"\n✅ Found branch: {branch.name}")

# Get current vault balance
weekly_vault = WeeklyVault.objects.filter(branch=branch.name).first()
if not weekly_vault:
    print("\n❌ Weekly vault record not found for KUKU!")
    exit()

print(f"\n📊 CURRENT VAULT RECORD:")
print(f"   Stored Balance: K{weekly_vault.balance}")

# Calculate actual balance from transactions
print(f"\n🔄 CALCULATING FROM TRANSACTIONS...")

transactions = VaultTransaction.objects.filter(
    branch__iexact=branch.name,
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

print(f"   Total IN:  K{total_in}")
print(f"   Total OUT: K{total_out}")
print(f"   Calculated Balance: K{calculated_balance}")
print(f"   Stored Balance:     K{weekly_vault.balance}")
print(f"   Difference:         K{calculated_balance - weekly_vault.balance}")

if calculated_balance == weekly_vault.balance:
    print(f"\n✅ Balance is already correct!")
    exit()

# Show the discrepancy
print(f"\n⚠️  BALANCE MISMATCH DETECTED!")
print(f"   The vault balance needs to be updated from K{weekly_vault.balance} to K{calculated_balance}")

# Ask for confirmation
response = input(f"\nUpdate vault balance to K{calculated_balance}? (yes/no): ")
if response.lower() != 'yes':
    print("\n❌ Aborted. No changes made.")
    exit()

# Update the balance
print(f"\n🔄 Updating vault balance...")

with transaction.atomic():
    weekly_vault.balance = calculated_balance
    weekly_vault.save()
    print(f"   ✅ Updated WeeklyVault balance to K{calculated_balance}")

# Verify
weekly_vault.refresh_from_db()
print(f"\n✅ VERIFIED:")
print(f"   New balance: K{weekly_vault.balance}")

print(f"\n💡 NEXT STEPS:")
print(f"1. Refresh the vault dashboard for KUKU branch")
print(f"2. Verify the weekly vault shows K{calculated_balance}")
print(f"3. Check that all loan disbursements are now recorded")

print(f"\n{'='*70}\n")
