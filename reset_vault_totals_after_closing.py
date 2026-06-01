#!/usr/bin/env python
"""
Reset vault inflows, outflows, and security deposits to match TODAY's transactions
(transactions that happened AFTER month closing).

This will:
1. Find all transactions AFTER month closing
2. Recalculate total inflows (sum of all IN transactions after closing)
3. Recalculate total outflows (sum of all OUT transactions after closing)
4. Recalculate security deposits (current security deposit balance)
5. Update vault models with correct totals
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from decimal import Decimal
from clients.models import Branch
from loans.models import DailyVault, WeeklyVault, Loan
from expenses.models import VaultTransaction
from datetime import datetime

def reset_vault_totals():
    """Reset vault inflows, outflows, and security deposits."""
    print("=" * 80)
    print("RESETTING VAULT TOTALS TO MATCH TODAY'S TRANSACTIONS")
    print("=" * 80)
    
    # Get today's date
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    summary = []
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"📍 BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        branch_inflows = Decimal('0.00')
        branch_outflows = Decimal('0.00')
        
        for vault_type in ['daily', 'weekly']:
            print(f"\n{'📅 DAILY' if vault_type == 'daily' else '📆 WEEKLY'} VAULT:")
            
            # Find the month closing transaction
            month_closing = VaultTransaction.objects.filter(
                branch__iexact=branch.name,
                vault_type=vault_type,
                transaction_type='month_close',
                transaction_date__gte=today_start
            ).first()
            
            if month_closing:
                # Get all transactions AFTER month closing
                after_closing = VaultTransaction.objects.filter(
                    branch__iexact=branch.name,
                    vault_type=vault_type,
                    transaction_date__gt=month_closing.transaction_date
                )
                print(f"   Month closing at: {month_closing.transaction_date.strftime('%H:%M:%S')}")
                print(f"   Transactions after closing: {after_closing.count()}")
            else:
                # No month closing, get all transactions from today
                after_closing = VaultTransaction.objects.filter(
                    branch__iexact=branch.name,
                    vault_type=vault_type,
                    transaction_date__gte=today_start
                )
                print(f"   No month closing found")
                print(f"   All transactions today: {after_closing.count()}")
            
            # Calculate inflows and outflows
            inflows = sum(
                tx.amount for tx in after_closing.filter(direction='in')
            )
            outflows = sum(
                tx.amount for tx in after_closing.filter(direction='out')
            )
            
            # Calculate balance
            balance = inflows - outflows
            
            print(f"   Inflows:  K{inflows:>12,.2f}")
            print(f"   Outflows: K{outflows:>12,.2f}")
            print(f"   Balance:  K{balance:>12,.2f}")
            
            # Update vault model
            if vault_type == 'daily':
                vault, _ = DailyVault.objects.get_or_create(branch=branch)
            else:
                vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
            
            vault.balance = balance
            vault.total_inflows = inflows
            vault.total_outflows = outflows
            vault.save(update_fields=['balance', 'total_inflows', 'total_outflows'])
            
            branch_inflows += inflows
            branch_outflows += outflows
        
        # Calculate security deposits for this branch
        # Get all active loans for this branch with security deposits
        try:
            loans_with_security = Loan.objects.filter(
                borrower__officer__branch=branch,
                status__in=['pending', 'approved', 'active', 'overdue'],
                security_deposit__gt=0
            )
            
            total_security = sum(loan.security_deposit for loan in loans_with_security)
        except Exception as e:
            # If there's an error getting loans, just use 0 for security deposits
            print(f"   ⚠️  Could not calculate security deposits: {e}")
            loans_with_security = []
            total_security = Decimal('0.00')
        
        print(f"\n💰 SECURITY DEPOSITS:")
        print(f"   Active loans with security: {loans_with_security.count()}")
        print(f"   Total security held: K{total_security:>12,.2f}")
        
        # Update security deposit on both vaults
        daily_vault = DailyVault.objects.filter(branch=branch).first()
        weekly_vault = WeeklyVault.objects.filter(branch=branch).first()
        
        if daily_vault:
            daily_vault.security_deposits = total_security
            daily_vault.save(update_fields=['security_deposits'])
        
        if weekly_vault:
            weekly_vault.security_deposits = total_security
            weekly_vault.save(update_fields=['security_deposits'])
        
        # Add to summary
        daily_balance = daily_vault.balance if daily_vault else Decimal('0.00')
        weekly_balance = weekly_vault.balance if weekly_vault else Decimal('0.00')
        total_balance = daily_balance + weekly_balance
        
        summary.append({
            'branch': branch.name,
            'daily_balance': daily_balance,
            'weekly_balance': weekly_balance,
            'total_balance': total_balance,
            'inflows': branch_inflows,
            'outflows': branch_outflows,
            'security': total_security,
        })
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY - ALL BRANCHES")
    print("=" * 80)
    
    for s in summary:
        print(f"\n📍 {s['branch']}")
        print(f"   Daily Vault:     K{s['daily_balance']:>12,.2f}")
        print(f"   Weekly Vault:    K{s['weekly_balance']:>12,.2f}")
        print(f"   Total Balance:   K{s['total_balance']:>12,.2f}")
        print(f"   Inflows:         K{s['inflows']:>12,.2f}")
        print(f"   Outflows:        K{s['outflows']:>12,.2f}")
        print(f"   Security Held:   K{s['security']:>12,.2f}")
    
    print("\n" + "=" * 80)
    print("✅ Vault totals have been reset to match today's transactions")
    print("✅ Inflows and outflows now reflect transactions after month closing")
    print("✅ Security deposits updated to match active loans")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    reset_vault_totals()
