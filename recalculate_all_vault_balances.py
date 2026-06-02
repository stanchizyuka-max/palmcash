#!/usr/bin/env python
"""
Recalculate all vault balances from transactions for June 1, 2026.
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
    print("RECALCULATE ALL VAULT BALANCES")
    print("=" * 80)
    
    today = date(2026, 6, 1)
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    print(f"\nProcessing {branches.count()} branch(es)...")
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"📍 {branch.name}")
        print('=' * 80)
        
        for vault_type in ['daily', 'weekly']:
            # Get ALL transactions for this vault from June 1, in chronological order
            transactions = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                vault_type=vault_type,
                transaction_date__gte=today_start
            ).order_by('transaction_date', 'id')
            
            if not transactions.exists():
                print(f"   {vault_type.capitalize()}: No transactions")
                continue
            
            # Recalculate balance_after for each transaction
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
                vault, created = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, created = WeeklyVault.objects.get_or_create(branch=branch)
            
            old_balance = vault.balance
            vault.balance = running_balance
            vault.total_inflows = inflows
            vault.total_outflows = outflows
            vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
            
            status = "✅" if running_balance >= 0 else "❌"
            change_indicator = ""
            if old_balance != running_balance:
                change_indicator = f" (was K{old_balance:,.2f})"
            
            print(f"   {vault_type.capitalize()}: K{running_balance:>10,.2f} {status}{change_indicator}")
            print(f"      Transactions: {transactions.count()}")
            print(f"      Inflows:  K{inflows:>10,.2f}")
            print(f"      Outflows: K{outflows:>10,.2f}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # Print final balances for all branches
    for branch in branches:
        try:
            daily = DailyVault.objects.get(branch=branch)
            daily_balance = daily.balance
        except DailyVault.DoesNotExist:
            daily_balance = Decimal('0.00')
        
        try:
            weekly = WeeklyVault.objects.get(branch=branch)
            weekly_balance = weekly.balance
        except WeeklyVault.DoesNotExist:
            weekly_balance = Decimal('0.00')
        
        total = daily_balance + weekly_balance
        status = "✅" if total >= 0 else "❌"
        
        print(f"\n{branch.name}:")
        print(f"   Daily:  K{daily_balance:>10,.2f}")
        print(f"   Weekly: K{weekly_balance:>10,.2f}")
        print(f"   Total:  K{total:>10,.2f} {status}")
    
    # Grand total
    all_daily = sum([v.balance for v in DailyVault.objects.filter(branch__in=branches)])
    all_weekly = sum([v.balance for v in WeeklyVault.objects.filter(branch__in=branches)])
    grand_total = all_daily + all_weekly
    
    print("\n" + "=" * 80)
    print(f"GRAND TOTAL: K{grand_total:,.2f}")
    print("=" * 80)
    
    print("\n✅ All vault balances have been recalculated and updated!")
    print("⚠️  Hard refresh your browser (Ctrl+Shift+R)")

if __name__ == '__main__':
    main()
