#!/usr/bin/env python
"""
Check the actual current state of vault transactions to understand what's wrong.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from clients.models import Branch
from loans.models import DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from datetime import datetime

def main():
    print("=" * 80)
    print("CHECKING ACTUAL VAULT STATE - JUNE 1, 2026")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"📍 BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        # Get vault balances from models
        try:
            daily_vault = DailyVault.objects.get(branch=branch)
            weekly_vault = WeeklyVault.objects.get(branch=branch)
            
            print(f"\n💰 VAULT MODEL BALANCES:")
            print(f"   Daily:  K{daily_vault.balance:>12,.2f}")
            print(f"   Weekly: K{weekly_vault.balance:>12,.2f}")
            print(f"   Total:  K{(daily_vault.balance + weekly_vault.balance):>12,.2f}")
        except:
            print("\n⚠️  Vault models not found")
        
        # Get all transactions from today
        all_txs = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_date__gte=today_start
        ).order_by('transaction_date', 'id')
        
        if not all_txs.exists():
            print("\n⚠️  No transactions found for today")
            continue
        
        print(f"\n📋 ALL TRANSACTIONS ({all_txs.count()} total):")
        print(f"{'─' * 80}")
        
        # Group by vault type
        for vault_type in ['daily', 'weekly']:
            vault_txs = all_txs.filter(vault_type=vault_type)
            
            if not vault_txs.exists():
                continue
            
            print(f"\n{'📅 DAILY' if vault_type == 'daily' else '📆 WEEKLY'} VAULT:")
            print(f"{'─' * 80}")
            
            for tx in vault_txs:
                direction_symbol = '▲' if tx.direction == 'in' else '▼'
                direction_text = 'IN' if tx.direction == 'in' else 'OUT'
                amount_text = f"+K{tx.amount:,.2f}" if tx.direction == 'in' else f"-K{tx.amount:,.2f}"
                
                # Check if this is a reversal
                is_reversal = 'REVERSAL:' in tx.description
                reversal_marker = ' [REVERSAL]' if is_reversal else ''
                
                print(f"\n   TX #{tx.id}: {tx.get_transaction_type_display()}{reversal_marker}")
                print(f"   {direction_symbol} {direction_text:3} {amount_text:>15} → Balance: K{tx.balance_after:>12,.2f}")
                print(f"   Time: {tx.transaction_date.strftime('%H:%M:%S')}")
                if tx.loan:
                    print(f"   Loan: {tx.loan.application_number}")
                if is_reversal:
                    print(f"   Description: {tx.description[:80]}")
        
        # Calculate what balances SHOULD be
        print(f"\n{'─' * 80}")
        print(f"📊 CALCULATED BALANCES (from transactions):")
        
        for vault_type in ['daily', 'weekly']:
            vault_txs = all_txs.filter(vault_type=vault_type)
            
            if not vault_txs.exists():
                continue
            
            # Calculate balance
            balance = sum(
                tx.amount if tx.direction == 'in' else -tx.amount
                for tx in vault_txs
            )
            
            # Calculate inflows/outflows
            inflows = sum(tx.amount for tx in vault_txs.filter(direction='in'))
            outflows = sum(tx.amount for tx in vault_txs.filter(direction='out'))
            
            vault_label = 'Daily' if vault_type == 'daily' else 'Weekly'
            print(f"\n   {vault_label}:")
            print(f"      Balance:  K{balance:>12,.2f}")
            print(f"      Inflows:  K{inflows:>12,.2f}")
            print(f"      Outflows: K{outflows:>12,.2f}")
            print(f"      Net:      K{(inflows - outflows):>12,.2f}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
