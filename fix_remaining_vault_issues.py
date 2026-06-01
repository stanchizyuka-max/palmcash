#!/usr/bin/env python
"""
Fix remaining vault issues after fixing payment collection directions.

Issues to fix:
1. KUKU: Month closing amounts are wrong (took out more than was in vault)
2. Chazanga: Has capital injection and security return that shouldn't be there
3. MANDEVU: Has capital injection and security return that shouldn't be there

This script will:
1. Delete capital injections and security returns added by fix scripts
2. Fix month closing amounts to match what was actually in the vault
3. Recalculate all balances
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

def delete_fix_transactions():
    """Delete capital injections and security returns added by fix scripts."""
    print("\n" + "=" * 80)
    print("STEP 1: DELETING FIX TRANSACTIONS")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    # Find capital injections and security returns from today
    fix_txs = VaultTransaction.objects.filter(
        transaction_date__gte=today_start,
        transaction_type__in=['capital_injection', 'security_return']
    ).exclude(
        description__icontains='REVERSAL'
    ).order_by('transaction_date', 'id')
    
    if not fix_txs.exists():
        print("✅ No fix transactions to delete")
        return
    
    print(f"⚠️  Found {fix_txs.count()} transaction(s) to delete:")
    
    for tx in fix_txs:
        print(f"\n   TX #{tx.id}: {tx.get_transaction_type_display()}")
        print(f"   Branch: {tx.branch}")
        print(f"   Vault: {tx.vault_type.upper()}")
        print(f"   Amount: K{tx.amount:,.2f}")
        print(f"   Direction: {tx.direction.upper()}")
    
    print(f"\n{'=' * 80}")
    response = input("Delete these transactions? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Skipping deletion")
        return False
    
    for tx in fix_txs:
        print(f"   Deleting TX #{tx.id}: {tx.get_transaction_type_display()} K{tx.amount:,.2f}")
        tx.delete()
    
    print(f"\n✅ Deleted {fix_txs.count()} transaction(s)")
    return True

def fix_month_closing_amounts():
    """Fix month closing amounts that are incorrect."""
    print("\n" + "=" * 80)
    print("STEP 2: FIXING MONTH CLOSING AMOUNTS")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    # Find all month closing transactions from today
    month_closings = VaultTransaction.objects.filter(
        transaction_type='month_close',
        transaction_date__gte=today_start
    ).order_by('branch', 'vault_type')
    
    if not month_closings.exists():
        print("✅ No month closing transactions found")
        return
    
    print(f"Found {month_closings.count()} month closing transaction(s)")
    
    for closing_tx in month_closings:
        print(f"\n{'─' * 80}")
        print(f"📍 {closing_tx.branch} - {'📅 DAILY' if closing_tx.vault_type == 'daily' else '📆 WEEKLY'}")
        print(f"   TX #{closing_tx.id}")
        print(f"   Current Amount: K{closing_tx.amount:,.2f}")
        print(f"   Balance After: K{closing_tx.balance_after:,.2f}")
        
        # The balance after month closing should be 0
        # So we need to set the amount to match what brings balance to 0
        # Get all transactions BEFORE this month closing
        prev_txs = VaultTransaction.objects.filter(
            branch__iexact=closing_tx.branch,
            vault_type=closing_tx.vault_type,
            transaction_date__lt=closing_tx.transaction_date
        ).order_by('transaction_date', 'id')
        
        # Calculate what the balance was before closing
        balance_before = Decimal('0.00')
        for tx in prev_txs:
            if tx.direction == 'in':
                balance_before += tx.amount
            else:
                balance_before -= tx.amount
        
        print(f"   Balance Before Closing: K{balance_before:,.2f}")
        
        # The closing amount should equal the balance before closing
        # (to bring balance to 0)
        correct_amount = balance_before
        
        if closing_tx.amount != correct_amount:
            print(f"   ⚠️  Incorrect! Should be K{correct_amount:,.2f}")
            closing_tx.amount = correct_amount
            closing_tx.balance_after = Decimal('0.00')
            closing_tx.save(update_fields=['amount', 'balance_after'])
            print(f"   ✅ Updated to K{correct_amount:,.2f}")
        else:
            print(f"   ✅ Already correct")

def recalculate_all_balances():
    """Recalculate all balances for all branches."""
    print("\n" + "=" * 80)
    print("STEP 3: RECALCULATING ALL BALANCES")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    summary = []
    
    for branch in branches:
        print(f"\n📍 {branch.name}")
        
        # Process each vault type
        for vault_type in ['daily', 'weekly']:
            # Get all transactions for this vault from today
            transactions = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                vault_type=vault_type,
                transaction_date__gte=today_start
            ).order_by('transaction_date', 'id')
            
            if not transactions.exists():
                continue
            
            # Recalculate balance_after for each transaction
            running_balance = Decimal('0.00')
            
            for tx in transactions:
                if tx.direction == 'in':
                    running_balance += tx.amount
                else:
                    running_balance -= tx.amount
                
                if tx.balance_after != running_balance:
                    tx.balance_after = running_balance
                    tx.save(update_fields=['balance_after'])
            
            # Calculate inflows and outflows
            inflows = sum(tx.amount for tx in transactions.filter(direction='in'))
            outflows = sum(tx.amount for tx in transactions.filter(direction='out'))
            
            # Update vault model
            if vault_type == 'daily':
                vault, _ = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            
            vault.balance = running_balance
            vault.total_inflows = inflows
            vault.total_outflows = outflows
            vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
            
            print(f"   {vault_type.capitalize()}: K{running_balance:>12,.2f} (In: K{inflows:,.2f}, Out: K{outflows:,.2f})")
        
        # Get final totals
        daily_vault = DailyVault.objects.filter(branch=branch).first()
        weekly_vault = WeeklyVault.objects.filter(branch=branch).first()
        
        daily_balance = daily_vault.balance if daily_vault else Decimal('0.00')
        weekly_balance = weekly_vault.balance if weekly_vault else Decimal('0.00')
        total_balance = daily_balance + weekly_balance
        
        summary.append({
            'branch': branch.name,
            'daily': daily_balance,
            'weekly': weekly_balance,
            'total': total_balance,
        })
    
    return summary

def main():
    print("=" * 80)
    print("FIXING REMAINING VAULT ISSUES")
    print("=" * 80)
    print("\n⚠️  This will:")
    print("   1. Delete capital injections and security returns")
    print("   2. Fix month closing amounts")
    print("   3. Recalculate all balances")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    # Step 1: Delete fix transactions
    deleted = delete_fix_transactions()
    
    # Step 2: Fix month closing amounts
    fix_month_closing_amounts()
    
    # Step 3: Recalculate all balances
    summary = recalculate_all_balances()
    
    # Print summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY - ALL BRANCHES")
    print("=" * 80)
    
    for s in summary:
        print(f"\n📍 {s['branch']}")
        print(f"   Daily:  K{s['daily']:>12,.2f}")
        print(f"   Weekly: K{s['weekly']:>12,.2f}")
        print(f"   Total:  K{s['total']:>12,.2f}")
    
    print("\n" + "=" * 80)
    print("✅ All vault issues have been fixed")
    print("✅ All balances have been recalculated")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
