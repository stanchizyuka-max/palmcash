#!/usr/bin/env python
"""
Fix Chazanga vault balance by recalculating from transaction log.
The vault balance is K0 but transactions show it should be K1,891 (or possibly K6,825).
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from loans.models import DailyVault, WeeklyVault
from clients.models import Branch
from django.db.models import Sum, Q
from decimal import Decimal

print("=" * 80)
print("CHAZANGA VAULT BALANCE FIX")
print("=" * 80)

branch_name = "Chazanga"
branch = Branch.objects.get(name=branch_name)

# Get current vault balances
daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)

print(f"\n📊 Current Vault Balances (BEFORE FIX):")
print(f"   Daily Vault:  K{daily_vault.balance:,.2f}")
print(f"   Weekly Vault: K{weekly_vault.balance:,.2f}")
print(f"   Total:        K{daily_vault.balance + weekly_vault.balance:,.2f}")

# Find last month closing
last_closing = VaultTransaction.objects.filter(
    branch__iexact=branch_name,
    transaction_type='month_close'
).order_by('-transaction_date').first()

if not last_closing:
    print(f"\n❌ No month closing found for {branch_name}")
    exit(1)

print(f"\n📅 Last Month Closing: {last_closing.transaction_date}")
print(f"   Opening Balance: K{last_closing.amount:,.2f}")

# Get all transactions after month closing
after_closing = VaultTransaction.objects.filter(
    branch__iexact=branch_name,
    transaction_date__gt=last_closing.transaction_date
).order_by('transaction_date')

print(f"\n📋 Analyzing {after_closing.count()} transactions after closing...")

# Calculate by vault type
daily_totals = after_closing.filter(vault_type='daily').aggregate(
    inflows=Sum('amount', filter=Q(direction='in')),
    outflows=Sum('amount', filter=Q(direction='out'))
)

weekly_totals = after_closing.filter(vault_type='weekly').aggregate(
    inflows=Sum('amount', filter=Q(direction='in')),
    outflows=Sum('amount', filter=Q(direction='out'))
)

daily_in = daily_totals['inflows'] or Decimal('0')
daily_out = daily_totals['outflows'] or Decimal('0')
daily_net = daily_in - daily_out

weekly_in = weekly_totals['inflows'] or Decimal('0')
weekly_out = weekly_totals['outflows'] or Decimal('0')
weekly_net = weekly_in - weekly_out

print(f"\n💰 Daily Vault Activity:")
print(f"   + Inflows:  K{daily_in:,.2f}")
print(f"   - Outflows: K{daily_out:,.2f}")
print(f"   = Net:      K{daily_net:,.2f}")

print(f"\n💰 Weekly Vault Activity:")
print(f"   + Inflows:  K{weekly_in:,.2f}")
print(f"   - Outflows: K{weekly_out:,.2f}")
print(f"   = Net:      K{weekly_net:,.2f}")

# Calculate what the balances should be
# Note: Opening balance from month closing needs to be allocated
# Check if there was a month closing transaction that specified vault type
daily_opening = Decimal('0')
weekly_opening = last_closing.amount  # Assume opening went to weekly vault

correct_daily_balance = daily_opening + daily_net
correct_weekly_balance = weekly_opening + weekly_net
correct_total = correct_daily_balance + correct_weekly_balance

print(f"\n✅ CORRECT Balances Should Be:")
print(f"   Daily Vault:  K{correct_daily_balance:,.2f}")
print(f"   Weekly Vault: K{correct_weekly_balance:,.2f}")
print(f"   Total:        K{correct_total:,.2f}")

# Show what needs to change
print(f"\n🔧 Changes Needed:")
print(f"   Daily:  K{daily_vault.balance:,.2f} → K{correct_daily_balance:,.2f} ({correct_daily_balance - daily_vault.balance:+,.2f})")
print(f"   Weekly: K{weekly_vault.balance:,.2f} → K{correct_weekly_balance:,.2f} ({correct_weekly_balance - weekly_vault.balance:+,.2f})")

# Prompt for confirmation
print(f"\n" + "=" * 80)
response = input("Apply these corrections? (yes/no): ").strip().lower()

if response == 'yes':
    # Update daily vault
    daily_vault.balance = correct_daily_balance
    daily_vault.save(update_fields=['balance'])
    
    # Update weekly vault
    weekly_vault.balance = correct_weekly_balance
    weekly_vault.save(update_fields=['balance'])
    
    print(f"\n✅ SUCCESS! Vault balances updated:")
    print(f"   Daily Vault:  K{correct_daily_balance:,.2f}")
    print(f"   Weekly Vault: K{correct_weekly_balance:,.2f}")
    print(f"   Total:        K{correct_total:,.2f}")
    
    # Verify
    daily_vault.refresh_from_db()
    weekly_vault.refresh_from_db()
    print(f"\n🔍 Verification:")
    print(f"   Daily Vault:  K{daily_vault.balance:,.2f} ✅")
    print(f"   Weekly Vault: K{weekly_vault.balance:,.2f} ✅")
    print(f"   Total:        K{daily_vault.balance + weekly_vault.balance:,.2f} ✅")
else:
    print(f"\n❌ Cancelled. No changes made.")

print("\n" + "=" * 80)
