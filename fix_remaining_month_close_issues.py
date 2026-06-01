#!/usr/bin/env python
"""
Fix remaining month closing issues after all branches were closed.
This script:
1. Resets all BranchSavings balances to K0.00
2. Verifies vault inflows/outflows are correct (should show only post-closing transactions)
3. Reports on security deposits (which come from vault transactions, not SecurityDeposit model)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db.models import Sum, Q
from decimal import Decimal
from clients.models import Branch
from loans.models import BranchSavings, DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from datetime import datetime

def main():
    print("=" * 80)
    print("FIXING REMAINING MONTH CLOSING ISSUES")
    print("=" * 80)
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        # 1. Check and reset BranchSavings balance
        print("\n1. CHECKING SAVINGS BALANCE...")
        savings, created = BranchSavings.objects.get_or_create(branch=branch)
        if savings.balance > 0:
            print(f"   ❌ Savings balance is K{savings.balance:,.2f} (should be K0.00)")
            print(f"   🔧 Resetting to K0.00...")
            savings.balance = Decimal('0.00')
            savings.save()
            print(f"   ✅ Savings balance reset to K0.00")
        else:
            print(f"   ✅ Savings balance is already K0.00")
        
        # 2. Check vault balances and inflows/outflows
        print("\n2. CHECKING VAULT BALANCES...")
        daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
        weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
        
        print(f"   Daily Vault Balance: K{daily_vault.balance:,.2f}")
        print(f"   Daily Vault Inflows: K{daily_vault.total_inflows:,.2f}")
        print(f"   Daily Vault Outflows: K{daily_vault.total_outflows:,.2f}")
        print(f"   Weekly Vault Balance: K{weekly_vault.balance:,.2f}")
        print(f"   Weekly Vault Inflows: K{weekly_vault.total_inflows:,.2f}")
        print(f"   Weekly Vault Outflows: K{weekly_vault.total_outflows:,.2f}")
        
        # 3. Find last month closing date
        print("\n3. CHECKING LAST MONTH CLOSING...")
        last_closing = VaultTransaction.objects.filter(
            branch=branch.name,
            transaction_type='month_close'
        ).order_by('-transaction_date').first()
        
        if last_closing:
            print(f"   ✅ Last closing: {last_closing.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}")
            closing_date = last_closing.transaction_date
            
            # Count transactions after closing
            txns_after_closing = VaultTransaction.objects.filter(
                branch=branch.name,
                transaction_date__gt=closing_date
            ).exclude(transaction_type='month_close')
            
            count = txns_after_closing.count()
            print(f"   📊 Transactions after closing: {count}")
            
            if count > 0:
                # Calculate inflows/outflows from transactions after closing
                totals = txns_after_closing.aggregate(
                    inflows=Sum('amount', filter=Q(direction='in')),
                    outflows=Sum('amount', filter=Q(direction='out'))
                )
                calc_inflows = totals['inflows'] or Decimal('0')
                calc_outflows = totals['outflows'] or Decimal('0')
                
                print(f"   📈 Calculated Inflows (from txns): K{calc_inflows:,.2f}")
                print(f"   📉 Calculated Outflows (from txns): K{calc_outflows:,.2f}")
                
                # Compare with vault counters
                total_vault_inflows = daily_vault.total_inflows + weekly_vault.total_inflows
                total_vault_outflows = daily_vault.total_outflows + weekly_vault.total_outflows
                
                if total_vault_inflows != calc_inflows or total_vault_outflows != calc_outflows:
                    print(f"   ⚠️  Vault counters don't match transaction totals!")
                    print(f"   🔧 Vault shows: Inflows K{total_vault_inflows:,.2f}, Outflows K{total_vault_outflows:,.2f}")
                else:
                    print(f"   ✅ Vault counters match transaction totals")
        else:
            print(f"   ⚠️  No month closing found for this branch")
        
        # 4. Check security deposits (from vault transactions)
        print("\n4. CHECKING SECURITY DEPOSITS (from vault transactions)...")
        security_in = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type='security_deposit',
            direction='in'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        security_out = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type__in=['security_return', 'security_used'],
            direction='out'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        security_balance = security_in - security_out
        
        print(f"   Security IN: K{security_in:,.2f}")
        print(f"   Security OUT: K{security_out:,.2f}")
        print(f"   Security Balance: K{security_balance:,.2f}")
        
        if security_balance > 0:
            print(f"   ℹ️  Security balance comes from vault transactions (not SecurityDeposit model)")
            print(f"   ℹ️  To reset this, you need to create security_return transactions")
            print(f"   ℹ️  Or manually adjust vault transactions if these are incorrect")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ All BranchSavings balances have been checked and reset if needed")
    print("✅ Vault balances and counters have been verified")
    print("ℹ️  Security deposits are calculated from vault transactions")
    print("ℹ️  If security deposits should be K0.00, you need to:")
    print("   1. Create security_return transactions for each security deposit")
    print("   2. Or delete incorrect security_deposit vault transactions")
    print("\n⚠️  IMPORTANT: After running this script, users should hard refresh (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
