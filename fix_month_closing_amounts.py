#!/usr/bin/env python
"""
Fix month closing transaction amounts.
The month closing transactions have incorrect amounts - they're taking out more
than what was in the vault, causing negative balances.

This script will:
1. Find all month closing transactions from June 1, 2026
2. Calculate what the correct amount should have been (balance before closing)
3. Update the transaction amounts
4. Recalculate all balance_after values
5. Update vault model balances
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

def fix_month_closing_for_branch(branch):
    """Fix month closing transactions for a specific branch."""
    print(f"\n{'=' * 80}")
    print(f"📍 BRANCH: {branch.name}")
    print(f"{'=' * 80}")
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    # Find month closing transactions from today
    month_closings = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        transaction_type='month_close',
        transaction_date__gte=today_start
    ).order_by('transaction_date', 'id')
    
    if not month_closings.exists():
        print("No month closing transactions found for today")
        return
    
    print(f"Found {month_closings.count()} month closing transaction(s)")
    
    for closing_tx in month_closings:
        vault_type = closing_tx.vault_type
        print(f"\n{'─' * 80}")
        print(f"{'📅 DAILY' if vault_type == 'daily' else '📆 WEEKLY'} VAULT MONTH CLOSING:")
        print(f"Transaction ID: {closing_tx.id}")
        print(f"Current Amount: K{closing_tx.amount:,.2f}")
        
        # Get the transaction immediately BEFORE this month closing
        prev_tx = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            vault_type=vault_type,
            transaction_date__lt=closing_tx.transaction_date
        ).order_by('-transaction_date', '-id').first()
        
        if not prev_tx:
            print("⚠️  No previous transaction found - cannot determine correct amount")
            continue
        
        # The correct closing amount should be the balance before closing
        correct_amount = prev_tx.balance_after
        
        print(f"Balance Before Closing: K{correct_amount:,.2f}")
        print(f"Difference: K{(closing_tx.amount - correct_amount):,.2f}")
        
        if closing_tx.amount != correct_amount:
            # Update the transaction amount
            closing_tx.amount = correct_amount
            closing_tx.save(update_fields=['amount'])
            print(f"✅ Updated closing amount to K{correct_amount:,.2f}")
        else:
            print(f"✅ Amount is already correct")

def recalculate_balances_for_branch(branch, vault_type):
    """Recalculate balance_after for all transactions after month closing."""
    
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
        return
    
    # Start with balance of 0 (beginning of day after month close)
    running_balance = Decimal('0.00')
    
    for tx in transactions:
        # Calculate new balance based on direction
        if tx.direction == 'in':
            running_balance += tx.amount
        else:  # 'out'
            running_balance -= tx.amount
        
        # Update balance_after if it changed
        if tx.balance_after != running_balance:
            tx.balance_after = running_balance
            tx.save(update_fields=['balance_after'])
    
    return running_balance

def main():
    print("=" * 80)
    print("FIXING MONTH CLOSING TRANSACTION AMOUNTS")
    print("=" * 80)
    print("\n⚠️  This will fix incorrect month closing amounts and recalculate balances")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    # Step 1: Fix month closing amounts
    print("\n" + "=" * 80)
    print("STEP 1: FIXING MONTH CLOSING AMOUNTS")
    print("=" * 80)
    
    for branch in branches:
        fix_month_closing_for_branch(branch)
    
    # Step 2: Recalculate all balances
    print("\n" + "=" * 80)
    print("STEP 2: RECALCULATING BALANCES")
    print("=" * 80)
    
    for branch in branches:
        print(f"\n📍 {branch.name}")
        
        # Recalculate daily vault
        daily_balance = recalculate_balances_for_branch(branch, 'daily')
        if daily_balance is not None:
            print(f"   Daily Vault: K{daily_balance:,.2f}")
            daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
            daily_vault.balance = daily_balance
            daily_vault.save(update_fields=['balance'])
        
        # Recalculate weekly vault
        weekly_balance = recalculate_balances_for_branch(branch, 'weekly')
        if weekly_balance is not None:
            print(f"   Weekly Vault: K{weekly_balance:,.2f}")
            weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            weekly_vault.balance = weekly_balance
            weekly_vault.save(update_fields=['balance'])
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ Month closing amounts have been corrected")
    print("✅ All balances have been recalculated")
    print("✅ Vault model balances have been updated")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
