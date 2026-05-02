#!/usr/bin/env python
"""
Fix vault_type for ALL branches - handles both NULL and empty string
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from loans.models import DailyVault, WeeklyVault
from clients.models import Branch
from decimal import Decimal
from django.db import transaction as db_transaction

def fix_all_branches():
    print("=" * 70)
    print("FIX ALL BRANCHES - VAULT TYPE ASSIGNMENT")
    print("=" * 70)
    
    # Find ALL transactions without vault_type (NULL or empty string)
    missing_vault_type = VaultTransaction.objects.filter(
        vault_type__isnull=True
    ) | VaultTransaction.objects.filter(vault_type='')
    
    total_count = missing_vault_type.count()
    
    if total_count == 0:
        print("\n✓ All transactions already have vault_type!")
        return True
    
    print(f"\nFound {total_count} transactions without vault_type")
    print("\nTransactions by branch:")
    print("-" * 70)
    
    # Group by branch
    branches_affected = {}
    for tx in missing_vault_type:
        if tx.branch not in branches_affected:
            branches_affected[tx.branch] = []
        branches_affected[tx.branch].append(tx)
    
    for branch_name, txs in branches_affected.items():
        print(f"\n{branch_name}: {len(txs)} transactions")
        for tx in txs:
            print(f"  - {tx.transaction_date.date()} | {tx.get_transaction_type_display()} | "
                  f"{tx.direction} | K{tx.amount:,.2f}")
    
    # Ask for confirmation
    print("\n" + "=" * 70)
    response = input("\nAssign vault_type to these transactions? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Operation cancelled")
        return False
    
    # Assign vault_type
    print("\nAssigning vault_type...")
    print("-" * 70)
    
    with db_transaction.atomic():
        for tx in missing_vault_type:
            # Determine vault type based on transaction type and loan
            if tx.loan:
                # Use loan's type if available
                vault_type = 'weekly' if tx.loan.loan_type == 'weekly' else 'daily'
            elif tx.transaction_type in ['capital_injection', 'bank_withdrawal', 
                                           'fund_deposit', 'expense', 'bank_deposit_out']:
                # These typically go to weekly vault
                vault_type = 'weekly'
            elif tx.transaction_type in ['payment_collection']:
                # Collections default to weekly
                vault_type = 'weekly'
            else:
                # Default to weekly for everything else
                vault_type = 'weekly'
            
            tx.vault_type = vault_type
            tx.save(update_fields=['vault_type'])
            print(f"  ✓ {tx.branch} | {tx.get_transaction_type_display()} → {vault_type}")
    
    print(f"\n✓ Updated {total_count} transactions")
    
    # Now recalculate balances for affected branches
    print("\n" + "=" * 70)
    print("RECALCULATING BALANCES FOR AFFECTED BRANCHES")
    print("=" * 70)
    
    for branch_name in branches_affected.keys():
        print(f"\n{branch_name}:")
        print("-" * 70)
        
        branch = Branch.objects.filter(name=branch_name).first()
        if not branch:
            print(f"  ⚠️  Branch not found in database")
            continue
        
        for vault_type in ['daily', 'weekly']:
            # Get all transactions for this branch and vault type
            txs = VaultTransaction.objects.filter(
                branch=branch_name,
                vault_type=vault_type
            ).order_by('transaction_date', 'id')
            
            if not txs.exists():
                continue
            
            # Recalculate running balance
            running_balance = Decimal('0')
            total_in = Decimal('0')
            total_out = Decimal('0')
            
            for tx in txs:
                if tx.direction == 'in':
                    running_balance += tx.amount
                    total_in += tx.amount
                else:
                    running_balance -= tx.amount
                    total_out += tx.amount
                
                # Update balance_after
                tx.balance_after = running_balance
                tx.save(update_fields=['balance_after'])
            
            print(f"  {vault_type.upper()} Vault: K{running_balance:,.2f} "
                  f"({txs.count()} txs, +K{total_in:,.2f} / -K{total_out:,.2f})")
            
            # Update the vault model
            VaultModel = WeeklyVault if vault_type == 'weekly' else DailyVault
            vault, created = VaultModel.objects.get_or_create(branch=branch)
            
            vault.balance = running_balance
            vault.total_inflows = total_in
            vault.total_outflows = total_out
            vault.save(update_fields=['balance', 'total_inflows', 'total_outflows', 'updated_at'])
    
    print("\n" + "=" * 70)
    print("✓ ALL BRANCHES FIXED")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  - Fixed {total_count} transactions across {len(branches_affected)} branches")
    print(f"  - Recalculated balances for all affected vaults")
    print(f"  - All transactions now have vault_type assigned")
    
    return True

if __name__ == '__main__':
    try:
        success = fix_all_branches()
        if success:
            print("\n✅ You can now run cleanup_old_branchvault.py")
        else:
            print("\n⚠️  Fix not completed")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
