#!/usr/bin/env python
"""
Sync vault model balances with the last transaction's balance_after.
After recalculating balance_after values, the vault models need to be updated
to match the final balance from the last transaction.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from decimal import Decimal
from clients.models import Branch
from loans.models import DailyVault, WeeklyVault
from expenses.models import VaultTransaction

def sync_vault_balance(branch, vault_type):
    """Sync vault model balance with last transaction's balance_after."""
    
    # Get the last transaction for this vault (most recent)
    last_transaction = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        vault_type=vault_type
    ).order_by('-transaction_date', '-id').first()
    
    if not last_transaction:
        return None
    
    # Get the vault model
    if vault_type == 'daily':
        vault, _ = DailyVault.objects.get_or_create(branch=branch)
    else:
        vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
    
    old_balance = vault.balance
    new_balance = last_transaction.balance_after
    
    if old_balance != new_balance:
        vault.balance = new_balance
        vault.save(update_fields=['balance', 'updated_at'])
        return {
            'updated': True,
            'old_balance': old_balance,
            'new_balance': new_balance,
            'last_tx_id': last_transaction.id,
            'last_tx_date': last_transaction.transaction_date
        }
    else:
        return {
            'updated': False,
            'balance': old_balance
        }

def main():
    print("=" * 80)
    print("SYNCING VAULT MODEL BALANCES WITH TRANSACTIONS")
    print("=" * 80)
    print("\n⚠️  This will update vault model balances to match the last transaction")
    
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
        daily_result = sync_vault_balance(branch, 'daily')
        
        if daily_result:
            if daily_result['updated']:
                print(f"   Balance: K{daily_result['old_balance']:>12,.2f} → K{daily_result['new_balance']:>12,.2f} ✅ Updated")
                print(f"   Last TX: #{daily_result['last_tx_id']} on {daily_result['last_tx_date'].strftime('%Y-%m-%d %H:%M')}")
                total_updated += 1
            else:
                print(f"   Balance: K{daily_result['balance']:>12,.2f} ✅ Already correct")
        else:
            print(f"   No transactions found")
        
        # Weekly Vault
        print(f"\n📆 WEEKLY VAULT:")
        weekly_result = sync_vault_balance(branch, 'weekly')
        
        if weekly_result:
            if weekly_result['updated']:
                print(f"   Balance: K{weekly_result['old_balance']:>12,.2f} → K{weekly_result['new_balance']:>12,.2f} ✅ Updated")
                print(f"   Last TX: #{weekly_result['last_tx_id']} on {weekly_result['last_tx_date'].strftime('%Y-%m-%d %H:%M')}")
                total_updated += 1
            else:
                print(f"   Balance: K{weekly_result['balance']:>12,.2f} ✅ Already correct")
        else:
            print(f"   No transactions found")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if total_updated > 0:
        print(f"✅ Updated {total_updated} vault balance(s)")
    else:
        print("✅ All vault balances were already correct")
    
    print("✅ Vault model balances now match transaction history")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
