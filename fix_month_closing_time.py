#!/usr/bin/env python
"""
Fix month closing times to 10:43 AM for all branches.

Currently some branches have month closing at 23:59:59 (end of day),
which means no transactions after closing are visible.

This script will:
1. Find all month closing transactions from June 1, 2026
2. Change their time to 10:43:00 AM
3. Recalculate balance_after for all transactions after the new closing time
4. Update vault balances
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
from datetime import datetime, time

def fix_month_closing_times():
    """Change month closing times to 10:43 AM."""
    print("=" * 80)
    print("FIXING MONTH CLOSING TIMES")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    new_closing_time = timezone.make_aware(datetime.combine(today, time(10, 43, 0)))
    
    # Find all month closing transactions from today
    month_closings = VaultTransaction.objects.filter(
        transaction_type='month_close',
        transaction_date__gte=today_start
    ).order_by('branch', 'vault_type')
    
    print(f"\nFound {month_closings.count()} month closing transaction(s)")
    print(f"New closing time will be: 10:43:00 AM\n")
    
    for closing in month_closings:
        old_time = closing.transaction_date.strftime('%H:%M:%S')
        closing.transaction_date = new_closing_time
        closing.save(update_fields=['transaction_date'])
        
        print(f"✅ {closing.branch} - {closing.vault_type.upper()}: {old_time} → 10:43:00")
    
    print(f"\n✅ Updated {month_closings.count()} month closing time(s)")

def recalculate_balances_after_closing():
    """Recalculate balance_after for all transactions after 10:43 AM."""
    print("\n" + "=" * 80)
    print("RECALCULATING BALANCES AFTER 10:43 AM")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    closing_time = timezone.make_aware(datetime.combine(today, time(10, 43, 0)))
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    summary = []
    
    for branch in branches:
        print(f"\n📍 {branch.name}")
        
        for vault_type in ['daily', 'weekly']:
            # Get all transactions AFTER 10:43 AM
            after_closing = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                vault_type=vault_type,
                transaction_date__gt=closing_time
            ).order_by('transaction_date', 'id')
            
            if not after_closing.exists():
                print(f"   {vault_type.capitalize()}: No transactions after 10:43 AM")
                
                # Set balance to 0
                if vault_type == 'daily':
                    vault, _ = DailyVault.objects.get_or_create(branch=branch)
                else:
                    vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
                
                vault.balance = Decimal('0.00')
                vault.total_inflows = Decimal('0.00')
                vault.total_outflows = Decimal('0.00')
                vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
                continue
            
            print(f"   {vault_type.capitalize()}: {after_closing.count()} transaction(s) after 10:43 AM")
            
            # Recalculate balance_after starting from 0
            running_balance = Decimal('0.00')
            
            for tx in after_closing:
                if tx.direction == 'in':
                    running_balance += tx.amount
                else:
                    running_balance -= tx.amount
                
                tx.balance_after = running_balance
                tx.save(update_fields=['balance_after'])
            
            # Calculate inflows and outflows
            inflows = sum(tx.amount for tx in after_closing.filter(direction='in'))
            outflows = sum(tx.amount for tx in after_closing.filter(direction='out'))
            
            # Update vault model
            if vault_type == 'daily':
                vault, _ = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            
            vault.balance = running_balance
            vault.total_inflows = inflows
            vault.total_outflows = outflows
            vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
            
            print(f"      Balance: K{running_balance:,.2f} (In: K{inflows:,.2f}, Out: K{outflows:,.2f})")
        
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
    print("FIX MONTH CLOSING TIME TO 10:43 AM")
    print("=" * 80)
    print("\n⚠️  This will:")
    print("   1. Change all month closing times to 10:43:00 AM")
    print("   2. Recalculate balance_after for transactions after 10:43 AM")
    print("   3. Update vault balances to show post-closing transactions")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    # Step 1: Fix month closing times
    fix_month_closing_times()
    
    # Step 2: Recalculate balances
    summary = recalculate_balances_after_closing()
    
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
    print("✅ Month closing times have been set to 10:43 AM")
    print("✅ All balances have been recalculated")
    print("✅ Transactions after 10:43 AM are now visible")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
