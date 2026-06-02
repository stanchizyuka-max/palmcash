#!/usr/bin/env python
"""
Fix duplicate KAMWALA SOUTH Daily month closing transactions.
There are two month closings - one should be removed or fixed.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from decimal import Decimal
from clients.models import Branch
from loans.models import DailyVault
from expenses.models import VaultTransaction
from datetime import datetime, date

def main():
    print("=" * 80)
    print("FIX DUPLICATE KAMWALA SOUTH DAILY MONTH CLOSING")
    print("=" * 80)
    
    today = date(2026, 6, 1)
    
    # Find all month closing transactions for KAMWALA SOUTH Daily
    month_closings = VaultTransaction.objects.filter(
        transaction_type='month_close',
        transaction_date__date=today,
        branch__iexact='KAMWALA SOUTH',
        vault_type='daily'
    ).order_by('transaction_date', 'id')
    
    print(f"\nFound {month_closings.count()} month closing transaction(s) for KAMWALA SOUTH Daily:")
    
    for tx in month_closings:
        print(f"\n   TX #{tx.id}:")
        print(f"   Time: {tx.transaction_date.strftime('%H:%M:%S')}")
        print(f"   Direction: {tx.direction.upper()}")
        print(f"   Amount: K{tx.amount:,.2f}")
        print(f"   Reference: {tx.reference_number}")
    
    if month_closings.count() <= 1:
        print("\n✅ Only one month closing found - no duplicates to fix")
        return
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    print("\nThe vault should have only ONE month closing transaction showing the")
    print("opening balance for June 1, 2026.")
    print("\nOptions:")
    print("1. Delete the K7,505.00 OUT transaction (it's a duplicate from old month closing)")
    print("2. Change the K7,505.00 OUT to IN (if it's the correct opening balance)")
    print("3. Keep the K100.00 IN and delete the K7,505.00 OUT")
    
    print("\n❓ Which month closing amount is correct for KAMWALA SOUTH Daily?")
    print("   - K100.00 (from TX #1824)")
    print("   - K7,505.00 (from TX #1831)")
    
    response = input("\nDo you want to DELETE the K7,505.00 OUT transaction? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        print("\nAlternatively, you can:")
        print("1. Change it to IN direction")
        print("2. Verify which amount is the correct opening balance")
        return
    
    # Delete the K7,505.00 OUT transaction
    tx_to_delete = month_closings.filter(
        direction='out',
        amount=Decimal('7505.00')
    ).first()
    
    if not tx_to_delete:
        print("\n❌ Could not find the K7,505.00 OUT transaction to delete")
        return
    
    print("\n" + "=" * 80)
    print("DELETING DUPLICATE TRANSACTION")
    print("=" * 80)
    
    print(f"\n🗑️  Deleting TX #{tx_to_delete.id}: {tx_to_delete.get_transaction_type_display()} "
          f"OUT K{tx_to_delete.amount:,.2f}")
    
    tx_to_delete.delete()
    
    print("✅ Transaction deleted")
    
    # Recalculate balances
    print("\n" + "=" * 80)
    print("RECALCULATING BALANCES")
    print("=" * 80)
    
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    branch = Branch.objects.filter(name__iexact='KAMWALA SOUTH').first()
    branch_name = branch.name if branch else 'KAMWALA SOUTH'
    
    transactions = VaultTransaction.objects.filter(
        branch__iexact=branch_name,
        vault_type='daily',
        transaction_date__gte=today_start
    ).order_by('transaction_date', 'id')
    
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
    print(f"\n💰 KAMWALA SOUTH Daily Vault: K{running_balance:,.2f}")
    
    if running_balance >= 0:
        print("✅ Balance is now POSITIVE!")
    else:
        print("⚠️  Balance is still negative")
    
    print("\n⚠️  Hard refresh your browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
