#!/usr/bin/env python
"""
Fix payment collection transactions that have the wrong direction.
Payment collections should ALWAYS be IN (inflow), not OUT (outflow).

This script will:
1. Find all payment collection transactions from June 1, 2026 with direction OUT
2. Change their direction to IN
3. Recalculate all balance_after values
4. Update vault model balances
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

def fix_payment_directions_for_branch(branch):
    """Fix payment collection directions for a specific branch."""
    print(f"\n{'=' * 80}")
    print(f"📍 BRANCH: {branch.name}")
    print(f"{'=' * 80}")
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    # Find payment collections with direction OUT (wrong!)
    wrong_payments = VaultTransaction.objects.filter(
        branch__iexact=branch.name,
        transaction_type='payment_collection',
        direction='out',
        transaction_date__gte=today_start
    ).order_by('transaction_date', 'id')
    
    if not wrong_payments.exists():
        print("✅ No payment collections with wrong direction found")
        return
    
    print(f"⚠️  Found {wrong_payments.count()} payment collection(s) with direction OUT (should be IN)")
    
    for tx in wrong_payments:
        print(f"\n   TX #{tx.id}:")
        print(f"   Loan: {tx.loan.application_number if tx.loan else 'N/A'}")
        print(f"   Amount: K{tx.amount:,.2f}")
        print(f"   Current Direction: {tx.direction.upper()}")
        print(f"   Vault: {tx.vault_type.upper()}")
        
        # Change direction to IN
        tx.direction = 'in'
        tx.save(update_fields=['direction'])
        print(f"   ✅ Changed direction to IN")

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
        return Decimal('0.00')
    
    # Start with balance of 0 (beginning of day after month close)
    running_balance = Decimal('0.00')
    
    print(f"\n   Recalculating {vault_type.upper()} vault balances:")
    
    for tx in transactions:
        # Calculate new balance based on direction
        if tx.direction == 'in':
            running_balance += tx.amount
        else:  # 'out'
            running_balance -= tx.amount
        
        # Update balance_after if it changed
        if tx.balance_after != running_balance:
            old_balance = tx.balance_after
            tx.balance_after = running_balance
            tx.save(update_fields=['balance_after'])
            print(f"      TX #{tx.id}: {tx.get_transaction_type_display()} - "
                  f"Balance: K{old_balance:,.2f} → K{running_balance:,.2f}")
    
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
    print("FIXING PAYMENT COLLECTION DIRECTIONS")
    print("=" * 80)
    print("\n⚠️  This will fix payment collections that have direction OUT (should be IN)")
    print("⚠️  and recalculate all balances")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    # Step 1: Fix payment collection directions
    print("\n" + "=" * 80)
    print("STEP 1: FIXING PAYMENT COLLECTION DIRECTIONS")
    print("=" * 80)
    
    for branch in branches:
        fix_payment_directions_for_branch(branch)
    
    # Step 2: Recalculate all balances
    print("\n" + "=" * 80)
    print("STEP 2: RECALCULATING BALANCES")
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
            'daily_inflows': daily_inflows,
            'daily_outflows': daily_outflows,
            'weekly_inflows': weekly_inflows,
            'weekly_outflows': weekly_outflows,
        })
        
        print(f"\n   Final Balances:")
        print(f"   Daily Vault:  K{daily_balance:>12,.2f} (In: K{daily_inflows:,.2f}, Out: K{daily_outflows:,.2f})")
        print(f"   Weekly Vault: K{weekly_balance:>12,.2f} (In: K{weekly_inflows:,.2f}, Out: K{weekly_outflows:,.2f})")
        print(f"   Total:        K{total_balance:>12,.2f}")
    
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
    print("✅ Payment collection directions have been corrected")
    print("✅ All balances have been recalculated")
    print("✅ Vault model balances have been updated")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
