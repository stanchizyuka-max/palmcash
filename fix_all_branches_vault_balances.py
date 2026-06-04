#!/usr/bin/env python
"""
Fix vault balances for ALL branches by recalculating from transaction log.
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
print("FIX ALL BRANCHES VAULT BALANCES")
print("=" * 80)

branches = Branch.objects.filter(is_active=True).order_by('name')
fixes_needed = []

# First, scan all branches to see what needs fixing
for branch in branches:
    # Get current vault balances
    daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
    weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
    
    current_daily = daily_vault.balance
    current_weekly = weekly_vault.balance
    current_total = current_daily + current_weekly
    
    # Find last month closing
    last_closing = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        transaction_type='month_close'
    ).order_by('-transaction_date').first()
    
    if not last_closing:
        continue
    
    # Get all transactions after month closing
    after_closing = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        transaction_date__gt=last_closing.transaction_date
    )
    
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
    daily_opening = Decimal('0')
    weekly_opening = last_closing.amount
    
    correct_daily = daily_opening + daily_net
    correct_weekly = weekly_opening + weekly_net
    correct_total = correct_daily + correct_weekly
    
    # Check for discrepancies
    daily_diff = current_daily - correct_daily
    weekly_diff = current_weekly - correct_weekly
    total_diff = current_total - correct_total
    
    if daily_diff != 0 or weekly_diff != 0:
        fixes_needed.append({
            'branch': branch,
            'daily_vault': daily_vault,
            'weekly_vault': weekly_vault,
            'current_daily': current_daily,
            'current_weekly': current_weekly,
            'current_total': current_total,
            'correct_daily': correct_daily,
            'correct_weekly': correct_weekly,
            'correct_total': correct_total,
            'diff_daily': daily_diff,
            'diff_weekly': weekly_diff,
            'diff_total': total_diff,
        })

if not fixes_needed:
    print("\n✅ ALL BRANCHES ARE ALREADY BALANCED!")
    print("   No fixes needed.")
    exit(0)

# Show what needs fixing
print(f"\n❌ FOUND {len(fixes_needed)} BRANCH(ES) WITH DISCREPANCIES:")
print(f"\n{'Branch':<20} {'Current Total':<15} {'Correct Total':<15} {'Difference':<15}")
print("-" * 65)
for fix in fixes_needed:
    print(f"{fix['branch'].name:<20} K{fix['current_total']:>12,.2f} K{fix['correct_total']:>12,.2f} K{fix['diff_total']:>12,.2f}")

print(f"\n📋 DETAILED BREAKDOWN:")
for fix in fixes_needed:
    print(f"\n🏢 {fix['branch'].name}:")
    print(f"   Daily Vault:  K{fix['current_daily']:,.2f} → K{fix['correct_daily']:,.2f} ({fix['diff_daily']:+,.2f})")
    print(f"   Weekly Vault: K{fix['current_weekly']:,.2f} → K{fix['correct_weekly']:,.2f} ({fix['diff_weekly']:+,.2f})")
    print(f"   Total:        K{fix['current_total']:,.2f} → K{fix['correct_total']:,.2f} ({fix['diff_total']:+,.2f})")

# Prompt for confirmation
print(f"\n" + "=" * 80)
response = input("Apply these corrections to ALL branches? (yes/no): ").strip().lower()

if response == 'yes':
    print(f"\n🔧 Applying fixes...")
    
    for fix in fixes_needed:
        # Update daily vault
        fix['daily_vault'].balance = fix['correct_daily']
        fix['daily_vault'].save(update_fields=['balance'])
        
        # Update weekly vault
        fix['weekly_vault'].balance = fix['correct_weekly']
        fix['weekly_vault'].save(update_fields=['balance'])
        
        print(f"   ✅ {fix['branch'].name}: Daily K{fix['correct_daily']:,.2f}, Weekly K{fix['correct_weekly']:,.2f}, Total K{fix['correct_total']:,.2f}")
    
    print(f"\n✅ SUCCESS! All {len(fixes_needed)} branch(es) updated.")
    
    # Verify
    print(f"\n🔍 Verification:")
    all_good = True
    for fix in fixes_needed:
        fix['daily_vault'].refresh_from_db()
        fix['weekly_vault'].refresh_from_db()
        actual_total = fix['daily_vault'].balance + fix['weekly_vault'].balance
        if actual_total == fix['correct_total']:
            print(f"   ✅ {fix['branch'].name}: K{actual_total:,.2f}")
        else:
            print(f"   ❌ {fix['branch'].name}: Expected K{fix['correct_total']:,.2f}, Got K{actual_total:,.2f}")
            all_good = False
    
    if all_good:
        print(f"\n🎉 ALL BRANCHES SUCCESSFULLY CORRECTED!")
    else:
        print(f"\n⚠️  Some branches may need manual review")
else:
    print(f"\n❌ Cancelled. No changes made.")

print("\n" + "=" * 80)
