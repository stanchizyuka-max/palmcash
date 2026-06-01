#!/usr/bin/env python
"""
Recalculate balance_after values for all transactions after month closing.

The issue: balance_after values are incorrect because transactions were
processed in the wrong order.

This script will:
1. Find the month closing transaction for each vault
2. Recalculate balance_after for all transactions AFTER month closing
3. Start from K0.00 (after closing) and add/subtract each transaction
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

def recalculate_balances_after_closing():
    """Recalculate balance_after for all transactions after month closing."""
    print("=" * 80)
    print("RECALCULATING BALANCE AFTER VALUES")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"📍 BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        for vault_type in ['daily', 'weekly']:
            print(f"\n{'📅 DAILY' if vault_type == 'daily' else '📆 WEEKLY'} VAULT:")
            
            # Find the month closing transaction
            month_closing = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                vault_type=vault_type,
                transaction_type='month_close',
                transaction_date__gte=today_start
            ).first()
            
            if not month_closing:
                print(f"   ⚠️  No month closing found")
                
                # Get all transactions and recalculate from 0
                all_txs = VaultTransaction.objects.filter(
                    branch__iexact=branch.name,
                    vault_type=vault_type,
                    transaction_date__gte=today_start
                ).order_by('transaction_date', 'id')
                
                if not all_txs.exists():
                    print(f"   ✅ No transactions")
                    continue
                
                running_balance = Decimal('0.00')
                
                for tx in all_txs:
                    if tx.direction == 'in':
                        running_balance += tx.amount
                    else:
                        running_balance -= tx.amount
                    
                    if tx.balance_after != running_balance:
                        old_balance = tx.balance_after
                        tx.balance_after = running_balance
                        tx.save(update_fields=['balance_after'])
                        print(f"   TX #{tx.id}: {tx.get_transaction_type_display()} - "
                              f"K{old_balance:,.2f} → K{running_balance:,.2f}")
                
                # Update vault model
                if vault_type == 'daily':
                    vault, _ = DailyVault.objects.get_or_create(branch=branch)
                else:
                    vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
                
                vault.balance = running_balance
                vault.save(update_fields=['balance'])
                
                print(f"   ✅ Final balance: K{running_balance:,.2f}")
                continue
            
            print(f"   Month closing at: {month_closing.transaction_date.strftime('%H:%M:%S')}")
            print(f"   Month closing amount: K{month_closing.amount:,.2f}")
            
            # Get all transactions AFTER month closing
            after_closing = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                vault_type=vault_type,
                transaction_date__gt=month_closing.transaction_date
            ).order_by('transaction_date', 'id')
            
            if not after_closing.exists():
                print(f"   ✅ No transactions after closing")
                
                # Update vault model to 0
                if vault_type == 'daily':
                    vault, _ = DailyVault.objects.get_or_create(branch=branch)
                else:
                    vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
                
                vault.balance = Decimal('0.00')
                vault.save(update_fields=['balance'])
                continue
            
            # Start from 0 after month closing
            running_balance = Decimal('0.00')
            
            print(f"\n   Recalculating {after_closing.count()} transaction(s) after closing:")
            
            for tx in after_closing:
                if tx.direction == 'in':
                    running_balance += tx.amount
                else:
                    running_balance -= tx.amount
                
                if tx.balance_after != running_balance:
                    old_balance = tx.balance_after
                    tx.balance_after = running_balance
                    tx.save(update_fields=['balance_after'])
                    print(f"      TX #{tx.id}: {tx.get_transaction_type_display()} "
                          f"{tx.direction.upper()} K{tx.amount:,.2f} - "
                          f"Balance: K{old_balance:,.2f} → K{running_balance:,.2f}")
            
            # Update vault model
            if vault_type == 'daily':
                vault, _ = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            
            vault.balance = running_balance
            vault.save(update_fields=['balance'])
            
            print(f"\n   ✅ Final balance: K{running_balance:,.2f}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for branch in branches:
        daily_vault = DailyVault.objects.filter(branch=branch).first()
        weekly_vault = WeeklyVault.objects.filter(branch=branch).first()
        
        daily_balance = daily_vault.balance if daily_vault else Decimal('0.00')
        weekly_balance = weekly_vault.balance if weekly_vault else Decimal('0.00')
        total_balance = daily_balance + weekly_balance
        
        print(f"\n📍 {branch.name}")
        print(f"   Daily:  K{daily_balance:>12,.2f}")
        print(f"   Weekly: K{weekly_balance:>12,.2f}")
        print(f"   Total:  K{total_balance:>12,.2f}")
    
    print("\n" + "=" * 80)
    print("✅ All balance_after values have been recalculated")
    print("✅ Vault model balances have been updated")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    recalculate_balances_after_closing()
