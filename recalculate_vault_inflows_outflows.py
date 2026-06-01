#!/usr/bin/env python
"""
Recalculate vault total_inflows and total_outflows from actual transactions.
This fixes incorrect inflow/outflow counters in the vault models.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db.models import Sum, Q
from decimal import Decimal
from clients.models import Branch
from loans.models import DailyVault, WeeklyVault
from expenses.models import VaultTransaction

def recalculate_vault_totals(branch, vault_type):
    """Recalculate inflows and outflows for a specific vault."""
    
    # Get all transactions for this vault
    transactions = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        vault_type=vault_type
    )
    
    # Calculate totals
    total_in = transactions.filter(direction='in').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_out = transactions.filter(direction='out').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Get the vault model
    if vault_type == 'daily':
        vault, _ = DailyVault.objects.get_or_create(branch=branch)
    else:
        vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
    
    # Store old values for comparison
    old_inflows = vault.total_inflows
    old_outflows = vault.total_outflows
    
    # Update the vault
    vault.total_inflows = total_in
    vault.total_outflows = total_out
    vault.save(update_fields=['total_inflows', 'total_outflows', 'updated_at'])
    
    return {
        'old_inflows': old_inflows,
        'new_inflows': total_in,
        'old_outflows': old_outflows,
        'new_outflows': total_out,
        'inflows_changed': old_inflows != total_in,
        'outflows_changed': old_outflows != total_out
    }

def main():
    print("=" * 80)
    print("RECALCULATING VAULT INFLOWS AND OUTFLOWS")
    print("=" * 80)
    print("\n⚠️  This will recalculate total_inflows and total_outflows for all vaults")
    print("⚠️  Based on actual vault transactions in the database")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    total_updated = 0
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"📍 BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        # Daily Vault
        print(f"\n📅 DAILY VAULT:")
        daily_result = recalculate_vault_totals(branch, 'daily')
        
        if daily_result['inflows_changed'] or daily_result['outflows_changed']:
            print(f"   Inflows:  K{daily_result['old_inflows']:>12,.2f} → K{daily_result['new_inflows']:>12,.2f} "
                  f"{'✅ Updated' if daily_result['inflows_changed'] else ''}")
            print(f"   Outflows: K{daily_result['old_outflows']:>12,.2f} → K{daily_result['new_outflows']:>12,.2f} "
                  f"{'✅ Updated' if daily_result['outflows_changed'] else ''}")
            if daily_result['inflows_changed']:
                total_updated += 1
            if daily_result['outflows_changed']:
                total_updated += 1
        else:
            print(f"   Inflows:  K{daily_result['new_inflows']:>12,.2f} ✅ Correct")
            print(f"   Outflows: K{daily_result['new_outflows']:>12,.2f} ✅ Correct")
        
        # Weekly Vault
        print(f"\n📆 WEEKLY VAULT:")
        weekly_result = recalculate_vault_totals(branch, 'weekly')
        
        if weekly_result['inflows_changed'] or weekly_result['outflows_changed']:
            print(f"   Inflows:  K{weekly_result['old_inflows']:>12,.2f} → K{weekly_result['new_inflows']:>12,.2f} "
                  f"{'✅ Updated' if weekly_result['inflows_changed'] else ''}")
            print(f"   Outflows: K{weekly_result['old_outflows']:>12,.2f} → K{weekly_result['new_outflows']:>12,.2f} "
                  f"{'✅ Updated' if weekly_result['outflows_changed'] else ''}")
            if weekly_result['inflows_changed']:
                total_updated += 1
            if weekly_result['outflows_changed']:
                total_updated += 1
        else:
            print(f"   Inflows:  K{weekly_result['new_inflows']:>12,.2f} ✅ Correct")
            print(f"   Outflows: K{weekly_result['new_outflows']:>12,.2f} ✅ Correct")
        
        # Calculate net for verification
        daily_net = daily_result['new_inflows'] - daily_result['new_outflows']
        weekly_net = weekly_result['new_inflows'] - weekly_result['new_outflows']
        
        print(f"\n💰 NET POSITIONS:")
        print(f"   Daily:  K{daily_net:>12,.2f}")
        print(f"   Weekly: K{weekly_net:>12,.2f}")
        print(f"   Total:  K{(daily_net + weekly_net):>12,.2f}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if total_updated > 0:
        print(f"✅ Updated {total_updated} inflow/outflow value(s)")
    else:
        print("✅ All inflow/outflow values were already correct")
    
    print("✅ All vault totals have been recalculated from actual transactions")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
