#!/usr/bin/env python
"""
Recalculate all "balance_after" values for vault transactions.
This fixes the incorrect balance calculations in the transaction history.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db.models import Q
from decimal import Decimal
from clients.models import Branch
from expenses.models import VaultTransaction
from loans.models import DailyVault, WeeklyVault

def recalculate_branch_balances(branch):
    """Recalculate balance_after for all transactions in a branch."""
    print(f"\n{'=' * 80}")
    print(f"BRANCH: {branch.name}")
    print(f"{'=' * 80}")
    
    # Get all transactions for this branch, ordered by date
    transactions = VaultTransaction.objects.filter(
        branch__iexact=branch.name
    ).order_by('transaction_date', 'id')
    
    total_count = transactions.count()
    print(f"Total transactions: {total_count}")
    
    if total_count == 0:
        print("No transactions found")
        return
    
    # Track balances for each vault type
    daily_balance = Decimal('0.00')
    weekly_balance = Decimal('0.00')
    
    updated_count = 0
    errors = []
    
    for tx in transactions:
        old_balance_after = tx.balance_after
        
        # Determine which vault this transaction affects
        vault_type = tx.vault_type or 'weekly'  # Default to weekly if not specified
        
        # Calculate new balance based on direction
        if tx.direction == 'in':
            amount_change = tx.amount
        else:  # 'out'
            amount_change = -tx.amount
        
        # Update the appropriate vault balance
        if vault_type == 'daily':
            daily_balance += amount_change
            new_balance_after = daily_balance
        else:  # 'weekly'
            weekly_balance += amount_change
            new_balance_after = weekly_balance
        
        # Update the transaction if balance changed
        if old_balance_after != new_balance_after:
            tx.balance_after = new_balance_after
            tx.save(update_fields=['balance_after'])
            updated_count += 1
            
            # Log significant changes
            if abs(old_balance_after - new_balance_after) > 100:
                print(f"  TX #{tx.id}: {tx.transaction_type} K{tx.amount} - "
                      f"Old: K{old_balance_after:,.2f} → New: K{new_balance_after:,.2f}")
    
    print(f"\n✅ Updated {updated_count} transactions")
    print(f"📊 Final balances:")
    print(f"   Daily Vault: K{daily_balance:,.2f}")
    print(f"   Weekly Vault: K{weekly_balance:,.2f}")
    
    # Update the vault models to match
    daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
    weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
    
    if daily_vault.balance != daily_balance:
        print(f"   ⚠️  Daily vault model shows K{daily_vault.balance:,.2f} but should be K{daily_balance:,.2f}")
        daily_vault.balance = daily_balance
        daily_vault.save()
        print(f"   ✅ Updated daily vault model")
    
    if weekly_vault.balance != weekly_balance:
        print(f"   ⚠️  Weekly vault model shows K{weekly_vault.balance:,.2f} but should be K{weekly_balance:,.2f}")
        weekly_vault.balance = weekly_balance
        weekly_vault.save()
        print(f"   ✅ Updated weekly vault model")
    
    return updated_count

def main():
    print("=" * 80)
    print("RECALCULATING ALL BALANCE AFTER VALUES")
    print("=" * 80)
    print("\n⚠️  This will recalculate the 'balance_after' column for all vault transactions")
    print("⚠️  This fixes incorrect balance calculations in transaction history")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    total_updated = 0
    
    for branch in branches:
        updated = recalculate_branch_balances(branch)
        total_updated += updated
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Total transactions updated: {total_updated}")
    print("✅ All balance_after values have been recalculated")
    print("✅ Vault model balances have been synchronized")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
