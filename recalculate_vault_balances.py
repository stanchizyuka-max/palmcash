#!/usr/bin/env python
"""
Recalculate balance_after for all vault transactions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from loans.models import DailyVault, WeeklyVault
from clients.models import Branch
from decimal import Decimal

print("=" * 80)
print("RECALCULATING VAULT TRANSACTION BALANCES")
print("=" * 80)

# Get all branches
branches = Branch.objects.all()

for branch in branches:
    print(f"\n{'=' * 80}")
    print(f"BRANCH: {branch.name}")
    print(f"{'=' * 80}")
    
    # Process Daily Vault
    print(f"\n📅 DAILY VAULT")
    print("-" * 80)
    
    daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
    daily_txs = VaultTransaction.objects.filter(
        branch=branch.name,
        vault_type='daily'
    ).order_by('transaction_date', 'id')
    
    if daily_txs.count() == 0:
        print("No transactions")
    else:
        print(f"Found {daily_txs.count()} transactions")
        
        # Start with 0 and recalculate
        running_balance = Decimal('0')
        
        for tx in daily_txs:
            # Calculate new balance
            if tx.direction == 'in':
                running_balance += tx.amount
            else:
                running_balance -= tx.amount
            
            # Update if different
            if tx.balance_after != running_balance:
                old_balance = tx.balance_after
                tx.balance_after = running_balance
                tx.save(update_fields=['balance_after'])
                print(f"  TX {tx.id}: {tx.transaction_date.date()} | {tx.get_transaction_type_display()} | {tx.direction}")
                print(f"    Amount: K{tx.amount:,.2f}")
                print(f"    Old balance_after: K{old_balance:,.2f}")
                print(f"    New balance_after: K{running_balance:,.2f} ✓")
        
        # Update vault balance to match final transaction
        if daily_vault.balance != running_balance:
            print(f"\n  Vault balance mismatch:")
            print(f"    Current: K{daily_vault.balance:,.2f}")
            print(f"    Calculated: K{running_balance:,.2f}")
            daily_vault.balance = running_balance
            daily_vault.save(update_fields=['balance', 'updated_at'])
            print(f"    ✓ Updated vault balance")
        else:
            print(f"\n  ✓ Vault balance correct: K{running_balance:,.2f}")
    
    # Process Weekly Vault
    print(f"\n📆 WEEKLY VAULT")
    print("-" * 80)
    
    weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
    weekly_txs = VaultTransaction.objects.filter(
        branch=branch.name,
        vault_type='weekly'
    ).order_by('transaction_date', 'id')
    
    if weekly_txs.count() == 0:
        print("No transactions")
    else:
        print(f"Found {weekly_txs.count()} transactions")
        
        # Start with 0 and recalculate
        running_balance = Decimal('0')
        
        for tx in weekly_txs:
            # Calculate new balance
            if tx.direction == 'in':
                running_balance += tx.amount
            else:
                running_balance -= tx.amount
            
            # Update if different
            if tx.balance_after != running_balance:
                old_balance = tx.balance_after
                tx.balance_after = running_balance
                tx.save(update_fields=['balance_after'])
                print(f"  TX {tx.id}: {tx.transaction_date.date()} | {tx.get_transaction_type_display()} | {tx.direction}")
                print(f"    Amount: K{tx.amount:,.2f}")
                print(f"    Old balance_after: K{old_balance:,.2f}")
                print(f"    New balance_after: K{running_balance:,.2f} ✓")
        
        # Update vault balance to match final transaction
        if weekly_vault.balance != running_balance:
            print(f"\n  Vault balance mismatch:")
            print(f"    Current: K{weekly_vault.balance:,.2f}")
            print(f"    Calculated: K{running_balance:,.2f}")
            weekly_vault.balance = running_balance
            weekly_vault.save(update_fields=['balance', 'updated_at'])
            print(f"    ✓ Updated vault balance")
        else:
            print(f"\n  ✓ Vault balance correct: K{running_balance:,.2f}")

print("\n" + "=" * 80)
print("✓ RECALCULATION COMPLETE")
print("=" * 80)
