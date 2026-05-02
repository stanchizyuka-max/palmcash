#!/usr/bin/env python
"""
Fix Kamwala south transactions specifically
This script finds transactions that are showing in the UI but not properly assigned to vaults
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

def fix_kamwala_transactions():
    print("=" * 70)
    print("KAMWALA SOUTH TRANSACTION FIX")
    print("=" * 70)
    
    branch_name = "Kamwala south"
    branch = Branch.objects.get(name=branch_name)
    
    # Get ALL transactions for Kamwala south
    all_txs = VaultTransaction.objects.filter(
        branch=branch_name
    ).order_by('transaction_date', 'id')
    
    print(f"\nTotal transactions for {branch_name}: {all_txs.count()}")
    
    # Show current state
    print("\nCurrent Transactions:")
    print("-" * 70)
    for tx in all_txs:
        vault_type_display = tx.vault_type if tx.vault_type else "❌ MISSING"
        print(f"{tx.transaction_date.date()} | {tx.get_transaction_type_display():20s} | "
              f"{tx.direction:3s} | K{tx.amount:>10,.2f} | Vault: {vault_type_display}")
    
    # Find transactions without vault_type
    missing_vault_type = all_txs.filter(vault_type__isnull=True) | all_txs.filter(vault_type='')
    
    if missing_vault_type.exists():
        print(f"\n⚠️  Found {missing_vault_type.count()} transactions without vault_type")
        print("\nAssigning vault_type to these transactions...")
        
        with db_transaction.atomic():
            for tx in missing_vault_type:
                # Determine vault type based on transaction type
                if tx.transaction_type in ['payment_collection', 'expense']:
                    # Collections and expenses typically weekly
                    vault_type = 'weekly'
                elif tx.transaction_type == 'capital_injection':
                    # Check description or default to weekly
                    vault_type = 'weekly'
                elif tx.loan:
                    # Use loan type if available
                    vault_type = 'weekly' if tx.loan.loan_type == 'weekly' else 'daily'
                else:
                    # Default to weekly
                    vault_type = 'weekly'
                
                print(f"  Setting {tx.get_transaction_type_display()} to {vault_type} vault")
                tx.vault_type = vault_type
                tx.save(update_fields=['vault_type'])
        
        print("✓ All transactions now have vault_type")
    else:
        print("\n✓ All transactions already have vault_type")
    
    # Now recalculate balances for each vault
    print("\n" + "=" * 70)
    print("RECALCULATING VAULT BALANCES")
    print("=" * 70)
    
    with db_transaction.atomic():
        for vault_type in ['daily', 'weekly']:
            print(f"\n{vault_type.upper()} VAULT:")
            print("-" * 70)
            
            # Get transactions for this vault type
            txs = VaultTransaction.objects.filter(
                branch=branch_name,
                vault_type=vault_type
            ).order_by('transaction_date', 'id')
            
            if not txs.exists():
                print(f"  No transactions")
                continue
            
            # Recalculate running balance
            running_balance = Decimal('0')
            total_in = Decimal('0')
            total_out = Decimal('0')
            
            print(f"  Processing {txs.count()} transactions:")
            for tx in txs:
                if tx.direction == 'in':
                    running_balance += tx.amount
                    total_in += tx.amount
                    symbol = "+"
                else:
                    running_balance -= tx.amount
                    total_out += tx.amount
                    symbol = "-"
                
                # Update balance_after
                old_balance = tx.balance_after
                tx.balance_after = running_balance
                tx.save(update_fields=['balance_after'])
                
                print(f"    {tx.transaction_date.date()} | {tx.get_transaction_type_display():20s} | "
                      f"{symbol}K{tx.amount:>8,.2f} → Balance: K{running_balance:>10,.2f}")
            
            print(f"\n  Summary:")
            print(f"    Total Inflows:  K{total_in:>10,.2f}")
            print(f"    Total Outflows: K{total_out:>10,.2f}")
            print(f"    Final Balance:  K{running_balance:>10,.2f}")
            
            # Update the vault model
            VaultModel = WeeklyVault if vault_type == 'weekly' else DailyVault
            vault, created = VaultModel.objects.get_or_create(branch=branch)
            
            old_vault_balance = vault.balance
            vault.balance = running_balance
            vault.total_inflows = total_in
            vault.total_outflows = total_out
            vault.save(update_fields=['balance', 'total_inflows', 'total_outflows', 'updated_at'])
            
            if old_vault_balance != running_balance:
                print(f"    ✓ Vault updated: K{old_vault_balance:,.2f} → K{running_balance:,.2f}")
            else:
                print(f"    ✓ Vault balance confirmed: K{running_balance:,.2f}")
    
    # Show final summary
    print("\n" + "=" * 70)
    print("FINAL VAULT BALANCES")
    print("=" * 70)
    
    try:
        daily = DailyVault.objects.get(branch=branch)
        print(f"Daily Vault:  K{daily.balance:>10,.2f}")
    except DailyVault.DoesNotExist:
        print(f"Daily Vault:  K{0:>10,.2f} (not created)")
    
    try:
        weekly = WeeklyVault.objects.get(branch=branch)
        print(f"Weekly Vault: K{weekly.balance:>10,.2f}")
    except WeeklyVault.DoesNotExist:
        print(f"Weekly Vault: K{0:>10,.2f} (not created)")
    
    # Calculate total
    daily_bal = DailyVault.objects.filter(branch=branch).first()
    weekly_bal = WeeklyVault.objects.filter(branch=branch).first()
    total = (daily_bal.balance if daily_bal else Decimal('0')) + (weekly_bal.balance if weekly_bal else Decimal('0'))
    print(f"{'─' * 30}")
    print(f"TOTAL:        K{total:>10,.2f}")
    
    print("\n" + "=" * 70)
    print("✓ FIX COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    try:
        fix_kamwala_transactions()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
