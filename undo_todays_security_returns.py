#!/usr/bin/env python
"""
UNDO security return transactions that were created today.
This reverses the security returns made by reset_security_deposits_after_month_close.py
so we can re-run it with the corrected logic that excludes today's transactions.
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

def main():
    print("=" * 80)
    print("UNDO TODAY'S SECURITY RETURN TRANSACTIONS")
    print("=" * 80)
    
    # Get today's date range
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    print(f"\nℹ️  Looking for security_return transactions from: {today_start.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find all security_return transactions created today
    todays_returns = VaultTransaction.objects.filter(
        transaction_type='security_return',
        transaction_date__gte=today_start,
        description__contains='Month closing security reset'
    ).order_by('branch', 'transaction_date')
    
    count = todays_returns.count()
    
    if count == 0:
        print("\n✅ No security return transactions found from today")
        print("   Nothing to undo!")
        return
    
    print(f"\n⚠️  Found {count} security return transaction(s) to undo:")
    for txn in todays_returns:
        print(f"   • {txn.branch}: K{txn.amount:,.2f} at {txn.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    response = input("\nDo you want to DELETE these transactions? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    print("\n🔧 Undoing transactions...")
    
    branches_affected = {}
    
    for txn in todays_returns:
        branch_name = txn.branch
        amount = txn.amount
        vault_type = txn.vault_type
        
        if branch_name not in branches_affected:
            branches_affected[branch_name] = {'daily': Decimal('0'), 'weekly': Decimal('0')}
        
        branches_affected[branch_name][vault_type] += amount
        
        print(f"   Deleting: {branch_name} {vault_type} vault K{amount:,.2f}")
        txn.delete()
    
    print("\n🔧 Restoring vault balances...")
    
    for branch_name, amounts in branches_affected.items():
        branch = Branch.objects.filter(name=branch_name).first()
        if not branch:
            print(f"   ⚠️  Branch '{branch_name}' not found - skipping")
            continue
        
        if amounts['daily'] > 0:
            daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
            old_balance = daily_vault.balance
            daily_vault.balance += amounts['daily']
            daily_vault.total_outflows -= amounts['daily']
            daily_vault.save()
            print(f"   ✅ {branch_name} Daily: K{old_balance:,.2f} → K{daily_vault.balance:,.2f}")
        
        if amounts['weekly'] > 0:
            weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            old_balance = weekly_vault.balance
            weekly_vault.balance += amounts['weekly']
            weekly_vault.total_outflows -= amounts['weekly']
            weekly_vault.save()
            print(f"   ✅ {branch_name} Weekly: K{old_balance:,.2f} → K{weekly_vault.balance:,.2f}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Deleted {count} security return transaction(s)")
    print(f"✅ Restored vault balances for {len(branches_affected)} branch(es)")
    print("\nℹ️  You can now re-run reset_security_deposits_after_month_close.py")
    print("   with the updated logic that excludes today's transactions")
    print("=" * 80)

if __name__ == '__main__':
    main()
