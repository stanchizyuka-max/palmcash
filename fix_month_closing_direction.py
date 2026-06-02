#!/usr/bin/env python
"""
Fix month closing transactions - they should show opening balance as INFLOW, not OUTFLOW.

The problem: Month closings were recorded as OUTFLOWS with the previous month's closing balance.
The solution: Change them to INFLOWS to represent the opening balance for the new month.
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
from datetime import datetime, date

def main():
    print("=" * 80)
    print("FIX MONTH CLOSING DIRECTION")
    print("=" * 80)
    
    print("\n⚠️  This script will:")
    print("   1. Change month closing transactions from OUT to IN")
    print("   2. Update descriptions to clarify they are opening balances")
    print("   3. Recalculate all balance_after values")
    print("   4. Update vault model balances")
    
    today = date(2026, 6, 1)
    
    # Find all month closing transactions
    month_closings = VaultTransaction.objects.filter(
        transaction_type='month_close',
        transaction_date__date=today
    ).order_by('branch', 'vault_type')
    
    print(f"\nFound {month_closings.count()} month closing transaction(s)")
    
    if month_closings.count() == 0:
        print("❌ No month closing transactions found")
        return
    
    print("\nCurrent state:")
    for tx in month_closings:
        print(f"   {tx.branch} - {tx.vault_type.upper()}: "
              f"Direction={tx.direction.upper()}, Amount=K{tx.amount:,.2f}")
    
    response = input("\nDo you want to fix these transactions? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    print("\n" + "=" * 80)
    print("FIXING MONTH CLOSING TRANSACTIONS")
    print("=" * 80)
    
    # Fix month closings
    for tx in month_closings:
        old_direction = tx.direction
        old_description = tx.description
        
        # Change direction from 'out' to 'in' (opening balance)
        tx.direction = 'in'
        
        # Update description to clarify this is opening balance
        if 'opening balance' not in tx.description.lower():
            tx.description = f"Month opening - Brought forward balance from May 2026: K{tx.amount:,.2f}"
        
        tx.save(update_fields=['direction', 'description'])
        
        print(f"✅ {tx.branch} - {tx.vault_type.upper()}: {old_direction.upper()} → IN (K{tx.amount:,.2f})")
    
    print(f"\n✅ Fixed {month_closings.count()} month closing transaction(s)")
    
    # Recalculate all balances
    print("\n" + "=" * 80)
    print("RECALCULATING BALANCES")
    print("=" * 80)
    
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    for branch in branches:
        print(f"\n📍 {branch.name}")
        
        for vault_type in ['daily', 'weekly']:
            # Get ALL transactions for this vault from today, in chronological order
            transactions = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                vault_type=vault_type,
                transaction_date__gte=today_start
            ).order_by('transaction_date', 'id')
            
            if not transactions.exists():
                print(f"   {vault_type.capitalize()}: No transactions")
                continue
            
            # Recalculate balance_after
            running_balance = Decimal('0.00')
            
            for tx in transactions:
                if tx.direction == 'in':
                    running_balance += tx.amount
                else:
                    running_balance -= tx.amount
                
                tx.balance_after = running_balance
                tx.save(update_fields=['balance_after'])
            
            # Calculate inflows and outflows
            inflows = sum(tx.amount for tx in transactions if tx.direction == 'in')
            outflows = sum(tx.amount for tx in transactions if tx.direction == 'out')
            
            # Update vault model
            if vault_type == 'daily':
                vault, _ = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            
            vault.balance = running_balance
            vault.total_inflows = inflows
            vault.total_outflows = outflows
            vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
            
            print(f"   {vault_type.capitalize()}: K{running_balance:,.2f} "
                  f"({transactions.count()} tx, In: K{inflows:,.2f}, Out: K{outflows:,.2f})")
    
    print("\n" + "=" * 80)
    print("FIX COMPLETE")
    print("=" * 80)
    print("\n✅ Month closing transactions changed to INFLOWS (opening balances)")
    print("✅ All balances recalculated")
    print("\n⚠️  IMPORTANT:")
    print("   - Month closings now show as opening balances (inflows)")
    print("   - This correctly represents bringing forward the previous month's balance")
    print("   - All vault balances should now be positive")
    print("\n⚠️  Hard refresh your browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
