#!/usr/bin/env python
"""
Fix KAMWALA SOUTH Daily month closing time from 23:59:59 to 10:43:00.

This will fix the remaining negative balance issue.
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
from datetime import datetime, date, time

def main():
    print("=" * 80)
    print("FIX KAMWALA SOUTH DAILY MONTH CLOSING TIME")
    print("=" * 80)
    
    print("\n⚠️  This script will:")
    print("   1. Change KAMWALA SOUTH Daily month closing time from 23:59:59 to 10:43:00")
    print("   2. Recalculate all balance_after values")
    print("   3. Update vault balances")
    
    today = date(2026, 6, 1)
    
    # Find the problematic month closing transaction
    problem_tx = VaultTransaction.objects.filter(
        transaction_type='month_close',
        transaction_date__date=today,
        branch__iexact='KAMWALA SOUTH',
        vault_type='daily'
    ).first()
    
    if not problem_tx:
        print("\n❌ Could not find KAMWALA SOUTH Daily month closing transaction")
        return
    
    print(f"\nFound transaction:")
    print(f"   TX #{problem_tx.id}: {problem_tx.branch} - {problem_tx.vault_type.upper()}")
    print(f"   Current time: {problem_tx.transaction_date.strftime('%H:%M:%S')}")
    print(f"   Amount: K{problem_tx.amount:,.2f}")
    print(f"   Direction: {problem_tx.direction.upper()}")
    
    if problem_tx.transaction_date.time() == time(10, 43, 0):
        print("\n✅ Transaction time is already 10:43:00 - no fix needed")
        return
    
    response = input("\nDo you want to fix this transaction? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    print("\n" + "=" * 80)
    print("FIXING TRANSACTION TIME")
    print("=" * 80)
    
    # Update the time
    old_time = problem_tx.transaction_date.strftime('%H:%M:%S')
    new_datetime = timezone.make_aware(datetime.combine(today, time(10, 43, 0)))
    problem_tx.transaction_date = new_datetime
    problem_tx.save(update_fields=['transaction_date'])
    
    print(f"✅ Changed time: {old_time} → 10:43:00")
    
    # Recalculate balances for KAMWALA SOUTH Daily vault
    print("\n" + "=" * 80)
    print("RECALCULATING BALANCES")
    print("=" * 80)
    
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    branch = Branch.objects.filter(name__iexact='KAMWALA SOUTH').first()
    if not branch:
        print("⚠️  Could not find KAMWALA SOUTH branch - using branch name from transaction")
        branch_name = 'KAMWALA SOUTH'
    else:
        branch_name = branch.name
    
    # Get ALL transactions for KAMWALA SOUTH Daily vault, in chronological order
    transactions = VaultTransaction.objects.filter(
        branch__iexact=branch_name,
        vault_type='daily',
        transaction_date__gte=today_start
    ).order_by('transaction_date', 'id')
    
    if not transactions.exists():
        print(f"❌ No transactions found for {branch_name} Daily vault")
        return
    
    # Recalculate balance_after
    running_balance = Decimal('0.00')
    
    print(f"\n📍 {branch_name} - DAILY")
    print("\nTransaction order:")
    
    for tx in transactions:
        if tx.direction == 'in':
            running_balance += tx.amount
            direction_symbol = "↑ IN "
        else:
            running_balance -= tx.amount
            direction_symbol = "↓ OUT"
        
        tx.balance_after = running_balance
        tx.save(update_fields=['balance_after'])
        
        print(f"   {tx.transaction_date.strftime('%H:%M:%S')} | "
              f"{tx.get_transaction_type_display():25s} | "
              f"{direction_symbol} K{tx.amount:>8,.2f} → Balance: K{running_balance:>10,.2f}")
    
    # Calculate inflows and outflows
    inflows = sum(tx.amount for tx in transactions if tx.direction == 'in')
    outflows = sum(tx.amount for tx in transactions if tx.direction == 'out')
    
    # Update vault model
    if branch:
        vault, _ = DailyVault.objects.get_or_create(branch=branch)
        vault.balance = running_balance
        vault.total_inflows = inflows
        vault.total_outflows = outflows
        vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
    
    print(f"\n✅ Final Balance: K{running_balance:,.2f}")
    print(f"   Total Inflows:  K{inflows:,.2f}")
    print(f"   Total Outflows: K{outflows:,.2f}")
    
    print("\n" + "=" * 80)
    print("FIX COMPLETE")
    print("=" * 80)
    print("\n✅ KAMWALA SOUTH Daily month closing time fixed")
    print("✅ Balance recalculated")
    print(f"\n💰 KAMWALA SOUTH Daily Vault: K{running_balance:,.2f}")
    
    if running_balance >= 0:
        print("✅ Balance is now POSITIVE!")
    else:
        print("⚠️  Balance is still negative - there may be other issues")
    
    print("\n⚠️  Hard refresh your browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
