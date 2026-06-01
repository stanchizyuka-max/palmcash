#!/usr/bin/env python
"""
Remove capital injection and security return transactions that were added
by previous fix scripts on June 1, 2026.

These transactions were added to fix negative balances, but now that we're
fixing the root cause (payment collection directions), we don't need them.

IMPORTANT: Only run this AFTER running fix_payment_collection_directions.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from decimal import Decimal
from clients.models import Branch
from loans.models import DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from datetime import datetime

def remove_fix_transactions_for_branch(branch):
    """Remove capital injection and security return transactions added by fix scripts."""
    print(f"\n{'=' * 80}")
    print(f"📍 BRANCH: {branch.name}")
    print(f"{'=' * 80}")
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    # Find capital injections and security returns from today
    # These were added by fix scripts and have specific patterns
    fix_txs = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        transaction_date__gte=today_start,
        transaction_type__in=['capital_injection', 'security_return'],
        recorded_by__username='admin'  # Assuming admin user ran the scripts
    ).order_by('transaction_date', 'id')
    
    if not fix_txs.exists():
        print("✅ No capital injection or security return transactions found")
        return
    
    print(f"⚠️  Found {fix_txs.count()} transaction(s) to remove:")
    
    for tx in fix_txs:
        print(f"\n   TX #{tx.id}:")
        print(f"   Type: {tx.get_transaction_type_display()}")
        print(f"   Direction: {tx.direction.upper()}")
        print(f"   Amount: K{tx.amount:,.2f}")
        print(f"   Vault: {tx.vault_type.upper()}")
        print(f"   Date: {tx.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return fix_txs

def recalculate_balances_for_branch(branch, vault_type):
    """Recalculate balance_after for all transactions after removing fix transactions."""
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    # Get all transactions for this vault from today, in chronological order
    transactions = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        vault_type=vault_type,
        transaction_date__gte=today_start
    ).order_by('transaction_date', 'id')
    
    if not transactions.exists():
        return Decimal('0.00')
    
    # Start with balance of 0 (beginning of day after month close)
    running_balance = Decimal('0.00')
    
    for tx in transactions:
        # Calculate new balance based on direction
        if tx.direction == 'in':
            running_balance += tx.amount
        else:  # 'out'
            running_balance -= tx.amount
        
        # Update balance_after
        tx.balance_after = running_balance
        tx.save(update_fields=['balance_after'])
    
    return running_balance

def recalculate_inflows_outflows(branch, vault_type):
    """Recalculate total inflows and outflows for a vault."""
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    # Get all transactions for this vault from today
    transactions = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        vault_type=vault_type,
        transaction_date__gte=today_start
    )
    
    # Calculate totals
    total_inflows = sum(
        tx.amount for tx in transactions.filter(direction='in')
    )
    total_outflows = sum(
        tx.amount for tx in transactions.filter(direction='out')
    )
    
    return total_inflows, total_outflows

def main():
    print("=" * 80)
    print("REMOVING CAPITAL INJECTION AND SECURITY RETURN TRANSACTIONS")
    print("=" * 80)
    print("\n⚠️  This will remove capital injections and security returns added by fix scripts")
    print("⚠️  ONLY run this AFTER running fix_payment_collection_directions.py")
    print("\n❓ Have you already run fix_payment_collection_directions.py?")
    
    response = input("Type 'yes' to continue: ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    # Step 1: Identify transactions to remove
    print("\n" + "=" * 80)
    print("STEP 1: IDENTIFYING TRANSACTIONS TO REMOVE")
    print("=" * 80)
    
    all_fix_txs = []
    for branch in branches:
        fix_txs = remove_fix_transactions_for_branch(branch)
        if fix_txs:
            all_fix_txs.extend(list(fix_txs))
    
    if not all_fix_txs:
        print("\n✅ No transactions to remove - you're all set!")
        return
    
    print(f"\n{'=' * 80}")
    print(f"⚠️  TOTAL: {len(all_fix_txs)} transaction(s) will be deleted")
    print(f"{'=' * 80}")
    
    response = input("\nAre you sure you want to delete these transactions? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    # Step 2: Delete the transactions
    print("\n" + "=" * 80)
    print("STEP 2: DELETING TRANSACTIONS")
    print("=" * 80)
    
    for tx in all_fix_txs:
        print(f"   Deleting TX #{tx.id}: {tx.get_transaction_type_display()} K{tx.amount:,.2f}")
        tx.delete()
    
    print(f"\n✅ Deleted {len(all_fix_txs)} transaction(s)")
    
    # Step 3: Recalculate all balances
    print("\n" + "=" * 80)
    print("STEP 3: RECALCULATING BALANCES")
    print("=" * 80)
    
    summary = []
    
    for branch in branches:
        print(f"\n📍 {branch.name}")
        
        # Recalculate daily vault
        daily_balance = recalculate_balances_for_branch(branch, 'daily')
        daily_inflows, daily_outflows = recalculate_inflows_outflows(branch, 'daily')
        
        daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
        daily_vault.balance = daily_balance
        daily_vault.total_inflows = daily_inflows
        daily_vault.total_outflows = daily_outflows
        daily_vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
        
        # Recalculate weekly vault
        weekly_balance = recalculate_balances_for_branch(branch, 'weekly')
        weekly_inflows, weekly_outflows = recalculate_inflows_outflows(branch, 'weekly')
        
        weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
        weekly_vault.balance = weekly_balance
        weekly_vault.total_inflows = weekly_inflows
        weekly_vault.total_outflows = weekly_outflows
        weekly_vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
        
        total_balance = daily_balance + weekly_balance
        
        summary.append({
            'branch': branch.name,
            'daily': daily_balance,
            'weekly': weekly_balance,
            'total': total_balance,
        })
        
        print(f"   Daily:  K{daily_balance:>12,.2f}")
        print(f"   Weekly: K{weekly_balance:>12,.2f}")
        print(f"   Total:  K{total_balance:>12,.2f}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY - ALL BRANCHES")
    print("=" * 80)
    
    for s in summary:
        print(f"\n📍 {s['branch']}")
        print(f"   Daily:  K{s['daily']:>12,.2f}")
        print(f"   Weekly: K{s['weekly']:>12,.2f}")
        print(f"   Total:  K{s['total']:>12,.2f}")
    
    print("\n" + "=" * 80)
    print("✅ Capital injections and security returns have been removed")
    print("✅ All balances have been recalculated")
    print("✅ Vault model balances have been updated")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
