#!/usr/bin/env python
"""
Verify KAMWALA SOUTH vault balances are correct
Check if displayed balances match actual transaction totals
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from loans.models import DailyVault, WeeklyVault
from clients.models import Branch
from decimal import Decimal
from django.db.models import Sum, Q

print("\n" + "="*70)
print("VERIFY KAMWALA SOUTH VAULT BALANCES")
print("="*70)

# Get the branch
branch = Branch.objects.filter(name__iexact='KAMWALA SOUTH').first()
if not branch:
    print("\n❌ KAMWALA SOUTH branch not found!")
    exit()

print(f"\n✅ Found branch: {branch.name}")

# Get the vaults
daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)

print(f"\n📊 CURRENT VAULT RECORDS:")
print(f"Daily Vault Balance:   K{daily_vault.balance}")
print(f"Weekly Vault Balance:  K{weekly_vault.balance}")
print(f"Total Balance:         K{daily_vault.balance + weekly_vault.balance}")

# Calculate from transactions
print(f"\n🔍 CALCULATING FROM TRANSACTIONS...")

# Daily vault transactions
daily_txs = VaultTransaction.objects.filter(
    branch__iexact='KAMWALA SOUTH',
    vault_type='daily'
)

daily_in = daily_txs.filter(direction='in').aggregate(
    total=Sum('amount')
)['total'] or Decimal('0')

daily_out = daily_txs.filter(direction='out').aggregate(
    total=Sum('amount')
)['total'] or Decimal('0')

daily_calculated = daily_in - daily_out

print(f"\nDaily Vault:")
print(f"  Total IN:  K{daily_in}")
print(f"  Total OUT: K{daily_out}")
print(f"  Calculated Balance: K{daily_calculated}")
print(f"  Stored Balance:     K{daily_vault.balance}")
print(f"  Difference:         K{daily_calculated - daily_vault.balance}")

if daily_calculated == daily_vault.balance:
    print(f"  ✅ Daily vault balance is CORRECT")
else:
    print(f"  ❌ Daily vault balance is INCORRECT")

# Weekly vault transactions
weekly_txs = VaultTransaction.objects.filter(
    branch__iexact='KAMWALA SOUTH',
    vault_type='weekly'
)

weekly_in = weekly_txs.filter(direction='in').aggregate(
    total=Sum('amount')
)['total'] or Decimal('0')

weekly_out = weekly_txs.filter(direction='out').aggregate(
    total=Sum('amount')
)['total'] or Decimal('0')

weekly_calculated = weekly_in - weekly_out

print(f"\nWeekly Vault:")
print(f"  Total IN:  K{weekly_in}")
print(f"  Total OUT: K{weekly_out}")
print(f"  Calculated Balance: K{weekly_calculated}")
print(f"  Stored Balance:     K{weekly_vault.balance}")
print(f"  Difference:         K{weekly_calculated - weekly_vault.balance}")

if weekly_calculated == weekly_vault.balance:
    print(f"  ✅ Weekly vault balance is CORRECT")
else:
    print(f"  ❌ Weekly vault balance is INCORRECT")

# Total
total_calculated = daily_calculated + weekly_calculated
total_stored = daily_vault.balance + weekly_vault.balance

print(f"\n📊 TOTAL:")
print(f"  Calculated Total: K{total_calculated}")
print(f"  Stored Total:     K{total_stored}")
print(f"  Difference:       K{total_calculated - total_stored}")

if total_calculated == total_stored:
    print(f"  ✅ Total balance is CORRECT")
else:
    print(f"  ❌ Total balance is INCORRECT")

# Check for reversals
print(f"\n🔍 CHECKING FOR REVERSALS...")

reversals = VaultTransaction.objects.filter(
    branch__iexact='KAMWALA SOUTH',
    description__icontains='REVERSAL'
)

if reversals.exists():
    print(f"\n⚠️  Found {reversals.count()} reversal transaction(s):")
    for rev in reversals[:5]:
        print(f"  - {rev.transaction_date.date()} | {rev.transaction_type} | K{rev.amount} | {rev.direction}")
else:
    print(f"\n✅ No reversal transactions found")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

all_correct = (
    daily_calculated == daily_vault.balance and
    weekly_calculated == weekly_vault.balance
)

if all_correct:
    print(f"\n✅ ALL BALANCES ARE CORRECT!")
    print(f"\nDaily Vault:  K{daily_vault.balance} ✅")
    print(f"Weekly Vault: K{weekly_vault.balance} ✅")
    print(f"Total:        K{total_stored} ✅")
else:
    print(f"\n❌ BALANCES ARE INCORRECT!")
    print(f"\nExpected:")
    print(f"  Daily Vault:  K{daily_calculated}")
    print(f"  Weekly Vault: K{weekly_calculated}")
    print(f"  Total:        K{total_calculated}")
    print(f"\nActual:")
    print(f"  Daily Vault:  K{daily_vault.balance}")
    print(f"  Weekly Vault: K{weekly_vault.balance}")
    print(f"  Total:        K{total_stored}")
    print(f"\nDifferences:")
    print(f"  Daily:  K{daily_calculated - daily_vault.balance}")
    print(f"  Weekly: K{weekly_calculated - weekly_vault.balance}")
    print(f"  Total:  K{total_calculated - total_stored}")

print("\n" + "="*70 + "\n")

