#!/usr/bin/env python
"""
Investigate Chazanga -K1,190 discrepancy
Why is actual balance K6,825 when it should be K8,015?
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from django.db.models import Sum, Q
from datetime import datetime
from django.utils import timezone
from decimal import Decimal

print("=" * 80)
print("CHAZANGA VAULT DISCREPANCY INVESTIGATION")
print("=" * 80)

branch_name = "Chazanga"

# Find last month closing
last_closing = VaultTransaction.objects.filter(
    branch__iexact=branch_name,
    transaction_type='month_close'
).order_by('-transaction_date').first()

if not last_closing:
    print(f"\n❌ No month closing found for {branch_name}")
    exit(1)

print(f"\n📅 Last Month Closing:")
print(f"   Date: {last_closing.transaction_date}")
print(f"   Opening Balance: K{last_closing.amount:,.2f}")
print(f"   Balance After: K{last_closing.balance_after:,.2f}")

# Get all transactions AFTER month closing
after_closing = VaultTransaction.objects.filter(
    branch__iexact=branch_name,
    transaction_date__gt=last_closing.transaction_date
).order_by('transaction_date')

print(f"\n📊 Transactions After Month Closing: {after_closing.count()}")

# Calculate totals
totals = after_closing.aggregate(
    inflows=Sum('amount', filter=Q(direction='in')),
    outflows=Sum('amount', filter=Q(direction='out'))
)

inflows = totals['inflows'] or Decimal('0')
outflows = totals['outflows'] or Decimal('0')
net = inflows - outflows

print(f"\n💰 Summary:")
print(f"   Opening Balance: K{last_closing.amount:,.2f}")
print(f"   + Inflows:       K{inflows:,.2f}")
print(f"   - Outflows:      K{outflows:,.2f}")
print(f"   = Net Change:    K{net:,.2f}")
print(f"   ---")
print(f"   Should Be:       K{last_closing.amount + net:,.2f}")

# Get current vault balance
from loans.models import DailyVault, WeeklyVault
from clients.models import Branch

branch = Branch.objects.get(name=branch_name)
daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
actual_balance = daily_vault.balance + weekly_vault.balance

print(f"   Actual Balance:  K{actual_balance:,.2f}")
print(f"   ---")
discrepancy = actual_balance - (last_closing.amount + net)
print(f"   ⚠️  Discrepancy:   K{discrepancy:,.2f}")

# Show breakdown by transaction type
print(f"\n📋 Inflows by Type:")
inflow_types = after_closing.filter(direction='in').values('transaction_type').annotate(
    total=Sum('amount')
).order_by('-total')

for item in inflow_types:
    tx_type = dict(VaultTransaction._meta.get_field('transaction_type').choices).get(
        item['transaction_type'], item['transaction_type']
    )
    print(f"   {tx_type:30s} K{item['total']:>10,.2f}")

print(f"\n📋 Outflows by Type:")
outflow_types = after_closing.filter(direction='out').values('transaction_type').annotate(
    total=Sum('amount')
).order_by('-total')

if outflow_types:
    for item in outflow_types:
        tx_type = dict(VaultTransaction._meta.get_field('transaction_type').choices).get(
            item['transaction_type'], item['transaction_type']
        )
        print(f"   {tx_type:30s} K{item['total']:>10,.2f}")
else:
    print("   (No outflows)")

# Check for reversals
reversals = after_closing.filter(description__icontains='REVERSAL')
print(f"\n🔄 Reversals: {reversals.count()}")
if reversals.count() > 0:
    reversal_totals = reversals.aggregate(
        inflows=Sum('amount', filter=Q(direction='in')),
        outflows=Sum('amount', filter=Q(direction='out'))
    )
    print(f"   Reversal Inflows:  K{reversal_totals['inflows'] or 0:,.2f}")
    print(f"   Reversal Outflows: K{reversal_totals['outflows'] or 0:,.2f}")

# Show last 10 transactions with running balance
print(f"\n📜 Last 10 Transactions (newest first):")
print(f"{'Date':<12} {'Type':<20} {'Dir':<4} {'Amount':>12} {'Balance After':>14}")
print("-" * 70)

last_10 = after_closing.order_by('-transaction_date')[:10]
for tx in last_10:
    tx_type = dict(VaultTransaction._meta.get_field('transaction_type').choices).get(
        tx.transaction_type, tx.transaction_type
    )
    direction = '▲ IN' if tx.direction == 'in' else '▼ OUT'
    date_str = tx.transaction_date.strftime('%b %d')
    print(f"{date_str:<12} {tx_type:<20} {direction:<4} K{tx.amount:>10,.2f} K{tx.balance_after:>12,.2f}")

# Check balance_after field consistency
print(f"\n🔍 Balance Consistency Check:")
last_tx = after_closing.order_by('-transaction_date').first()
if last_tx:
    print(f"   Last transaction balance_after: K{last_tx.balance_after:,.2f}")
    print(f"   Current vault balance:          K{actual_balance:,.2f}")
    if last_tx.balance_after != actual_balance:
        print(f"   ⚠️  MISMATCH! Difference: K{actual_balance - last_tx.balance_after:,.2f}")
    else:
        print(f"   ✅ Consistent")

print("\n" + "=" * 80)
