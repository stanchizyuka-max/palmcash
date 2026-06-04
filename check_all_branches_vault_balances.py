#!/usr/bin/env python
"""
Check ALL branches for vault balance discrepancies.
Compare database vault balances vs calculated balances from transactions.
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
print("ALL BRANCHES VAULT BALANCE CHECK")
print("=" * 80)

branches = Branch.objects.filter(is_active=True).order_by('name')
issues_found = []

for branch in branches:
    print(f"\n{'='*80}")
    print(f"🏢 BRANCH: {branch.name}")
    print(f"{'='*80}")
    
    # Get current vault balances
    daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
    weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
    
    current_daily = daily_vault.balance
    current_weekly = weekly_vault.balance
    current_total = current_daily + current_weekly
    
    print(f"\n📊 Current Database Balances:")
    print(f"   Daily Vault:  K{current_daily:,.2f}")
    print(f"   Weekly Vault: K{current_weekly:,.2f}")
    print(f"   Total:        K{current_total:,.2f}")
    
    # Find last month closing
    last_closing = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        transaction_type='month_close'
    ).order_by('-transaction_date').first()
    
    if not last_closing:
        print(f"   ⚠️  No month closing found")
        continue
    
    print(f"\n📅 Last Month Closing: {last_closing.transaction_date.strftime('%b %d, %Y %H:%M')}")
    print(f"   Opening Balance: K{last_closing.amount:,.2f}")
    
    # Get all transactions after month closing
    after_closing = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        transaction_date__gt=last_closing.transaction_date
    ).order_by('transaction_date')
    
    tx_count = after_closing.count()
    print(f"   Transactions Since: {tx_count}")
    
    if tx_count == 0:
        # No transactions since closing, balance should equal opening
        expected_total = last_closing.amount
        if current_total != expected_total:
            print(f"   ❌ MISMATCH: Expected K{expected_total:,.2f}, Got K{current_total:,.2f}")
            issues_found.append({
                'branch': branch.name,
                'expected': expected_total,
                'actual': current_total,
                'difference': current_total - expected_total
            })
        else:
            print(f"   ✅ Balance matches opening")
        continue
    
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
    
    # Calculate correct balances
    # Opening balance goes to weekly vault by default
    daily_opening = Decimal('0')
    weekly_opening = last_closing.amount
    
    correct_daily = daily_opening + daily_net
    correct_weekly = weekly_opening + weekly_net
    correct_total = correct_daily + correct_weekly
    
    print(f"\n💰 Activity Since Closing:")
    print(f"   Daily:  In K{daily_in:,.2f}, Out K{daily_out:,.2f}, Net K{daily_net:,.2f}")
    print(f"   Weekly: In K{weekly_in:,.2f}, Out K{weekly_out:,.2f}, Net K{weekly_net:,.2f}")
    
    print(f"\n✅ Expected Balances:")
    print(f"   Daily Vault:  K{correct_daily:,.2f}")
    print(f"   Weekly Vault: K{correct_weekly:,.2f}")
    print(f"   Total:        K{correct_total:,.2f}")
    
    # Check for discrepancies
    daily_diff = current_daily - correct_daily
    weekly_diff = current_weekly - correct_weekly
    total_diff = current_total - correct_total
    
    if daily_diff != 0 or weekly_diff != 0:
        print(f"\n❌ DISCREPANCY FOUND:")
        if daily_diff != 0:
            print(f"   Daily:  K{daily_diff:+,.2f} (should be K{correct_daily:,.2f}, is K{current_daily:,.2f})")
        if weekly_diff != 0:
            print(f"   Weekly: K{weekly_diff:+,.2f} (should be K{correct_weekly:,.2f}, is K{current_weekly:,.2f})")
        print(f"   Total:  K{total_diff:+,.2f}")
        
        issues_found.append({
            'branch': branch.name,
            'expected_daily': correct_daily,
            'actual_daily': current_daily,
            'diff_daily': daily_diff,
            'expected_weekly': correct_weekly,
            'actual_weekly': current_weekly,
            'diff_weekly': weekly_diff,
            'expected_total': correct_total,
            'actual_total': current_total,
            'diff_total': total_diff
        })
    else:
        print(f"\n✅ ALL GOOD - Balances match!")
    
    # Check last transaction balance_after vs current balance
    last_tx = after_closing.order_by('-transaction_date').first()
    if last_tx:
        print(f"\n🔍 Last Transaction Check:")
        print(f"   Last TX balance_after: K{last_tx.balance_after:,.2f}")
        print(f"   Current vault total:   K{current_total:,.2f}")
        if last_tx.balance_after != current_total:
            print(f"   ⚠️  MISMATCH! Difference: K{current_total - last_tx.balance_after:,.2f}")

# Summary
print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")

if not issues_found:
    print(f"\n✅ ALL BRANCHES ARE BALANCED!")
    print(f"   No discrepancies found.")
else:
    print(f"\n❌ ISSUES FOUND IN {len(issues_found)} BRANCH(ES):")
    print(f"\n{'Branch':<20} {'Expected':<15} {'Actual':<15} {'Difference':<15}")
    print("-" * 65)
    for issue in issues_found:
        print(f"{issue['branch']:<20} K{issue['expected_total']:>12,.2f} K{issue['actual_total']:>12,.2f} K{issue['diff_total']:>12,.2f}")
    
    print(f"\n⚠️  ACTION REQUIRED:")
    print(f"   Run the fix script to correct these balances:")
    print(f"   python fix_all_branches_vault_balances.py")

print("\n" + "=" * 80)
