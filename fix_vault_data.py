#!/usr/bin/env python
"""
Fix vault data after dual vault migration
This script:
1. Sets vault_type for all existing VaultTransactions that don't have it
2. Recalculates balances for all transactions in chronological order
3. Updates the DailyVault and WeeklyVault balances to match
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

def fix_vault_data():
    print("=" * 70)
    print("VAULT DATA FIX SCRIPT")
    print("=" * 70)
    
    # Get all active branches
    branches = Branch.objects.filter(is_active=True)
    
    for branch in branches:
        print(f"\n{'='*70}")
        print(f"Processing Branch: {branch.name}")
        print(f"{'='*70}")
        
        with db_transaction.atomic():
            # Step 1: Set vault_type for transactions that don't have it
            print("\nStep 1: Setting vault_type for existing transactions...")
            
            # Get all transactions for this branch without vault_type
            txs_without_type = VaultTransaction.objects.filter(
                branch=branch.name,
                vault_type__isnull=True
            )
            
            count = txs_without_type.count()
            if count > 0:
                print(f"  Found {count} transactions without vault_type")
                
                # Set default vault_type based on transaction type
                for tx in txs_without_type:
                    # Determine vault type based on transaction type and loan
                    if tx.loan:
                        # Use loan's type if available
                        vault_type = 'weekly' if tx.loan.loan_type == 'weekly' else 'daily'
                    elif tx.transaction_type in ['capital_injection', 'bank_withdrawal', 
                                                   'fund_deposit', 'expense']:
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
                
                print(f"  ✓ Updated {count} transactions with vault_type")
            else:
                print("  ✓ All transactions already have vault_type")
            
            # Step 2: Recalculate balances for each vault type
            print("\nStep 2: Recalculating balances...")
            
            for vault_type in ['daily', 'weekly']:
                print(f"\n  Processing {vault_type.upper()} vault:")
                
                # Get all transactions for this branch and vault type, ordered chronologically
                txs = VaultTransaction.objects.filter(
                    branch=branch.name,
                    vault_type=vault_type
                ).order_by('transaction_date', 'id')
                
                if not txs.exists():
                    print(f"    No transactions found for {vault_type} vault")
                    continue
                
                # Recalculate running balance
                running_balance = Decimal('0')
                total_inflows = Decimal('0')
                total_outflows = Decimal('0')
                
                for tx in txs:
                    if tx.direction == 'in':
                        running_balance += tx.amount
                        total_inflows += tx.amount
                    else:  # out
                        running_balance -= tx.amount
                        total_outflows += tx.amount
                    
                    # Update the balance_after field
                    if tx.balance_after != running_balance:
                        tx.balance_after = running_balance
                        tx.save(update_fields=['balance_after'])
                
                print(f"    Processed {txs.count()} transactions")
                print(f"    Total Inflows:  K{total_inflows:,.2f}")
                print(f"    Total Outflows: K{total_outflows:,.2f}")
                print(f"    Final Balance:  K{running_balance:,.2f}")
                
                # Step 3: Update the vault model to match
                VaultModel = WeeklyVault if vault_type == 'weekly' else DailyVault
                vault, created = VaultModel.objects.get_or_create(branch=branch)
                
                if vault.balance != running_balance:
                    print(f"    Vault balance mismatch detected!")
                    print(f"      Old balance: K{vault.balance:,.2f}")
                    print(f"      New balance: K{running_balance:,.2f}")
                    vault.balance = running_balance
                    vault.total_inflows = total_inflows
                    vault.total_outflows = total_outflows
                    vault.save(update_fields=['balance', 'total_inflows', 'total_outflows', 'updated_at'])
                    print(f"    ✓ Vault balance updated")
                else:
                    print(f"    ✓ Vault balance already correct")
    
    print("\n" + "=" * 70)
    print("VAULT DATA FIX COMPLETE")
    print("=" * 70)
    print("\nSummary:")
    print("  - All transactions now have vault_type set")
    print("  - All balance_after values recalculated in chronological order")
    print("  - All vault balances updated to match transaction history")
    print("\nYou can now view the vault page to see correct balances.")

if __name__ == '__main__':
    try:
        fix_vault_data()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
