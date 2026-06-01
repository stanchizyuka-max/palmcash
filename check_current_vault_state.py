#!/usr/bin/env python
"""
Check current state of all vaults, savings, and security deposits after month closing.
This provides a clear overview of what still needs to be fixed.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db.models import Sum
from decimal import Decimal
from clients.models import Branch
from loans.models import BranchSavings, DailyVault, WeeklyVault
from expenses.models import VaultTransaction

def main():
    print("=" * 80)
    print("CURRENT VAULT STATE - ALL BRANCHES")
    print("=" * 80)
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    issues_found = []
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"📍 BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        # Get vaults
        daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
        weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
        savings, _ = BranchSavings.objects.get_or_create(branch=branch)
        
        # Calculate security balance
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
        
        # Display current state
        print(f"\n💰 VAULT BALANCES:")
        print(f"   Daily Vault:  K{daily_vault.balance:>12,.2f} {'✅' if daily_vault.balance == 0 else '❌'}")
        print(f"   Weekly Vault: K{weekly_vault.balance:>12,.2f} {'✅' if weekly_vault.balance == 0 else '❌'}")
        print(f"   Total:        K{(daily_vault.balance + weekly_vault.balance):>12,.2f}")
        
        print(f"\n💵 SAVINGS:")
        print(f"   Balance:      K{savings.balance:>12,.2f} {'✅' if savings.balance == 0 else '❌'}")
        
        print(f"\n🔒 SECURITY DEPOSITS:")
        print(f"   Balance:      K{security_balance:>12,.2f} {'✅' if security_balance == 0 else '❌'}")
        
        print(f"\n📊 INFLOWS/OUTFLOWS:")
        print(f"   Daily Inflows:   K{daily_vault.total_inflows:>12,.2f}")
        print(f"   Daily Outflows:  K{daily_vault.total_outflows:>12,.2f}")
        print(f"   Weekly Inflows:  K{weekly_vault.total_inflows:>12,.2f}")
        print(f"   Weekly Outflows: K{weekly_vault.total_outflows:>12,.2f}")
        
        # Check for issues
        branch_issues = []
        if daily_vault.balance != 0:
            branch_issues.append(f"Daily vault balance: K{daily_vault.balance:,.2f}")
        if weekly_vault.balance != 0:
            branch_issues.append(f"Weekly vault balance: K{weekly_vault.balance:,.2f}")
        if savings.balance != 0:
            branch_issues.append(f"Savings balance: K{savings.balance:,.2f}")
        if security_balance != 0:
            branch_issues.append(f"Security deposits: K{security_balance:,.2f}")
        
        if branch_issues:
            issues_found.append({
                'branch': branch.name,
                'issues': branch_issues
            })
            print(f"\n⚠️  ISSUES FOUND:")
            for issue in branch_issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ ALL CLEAR - Everything is at K0.00")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if issues_found:
        print(f"\n❌ ISSUES FOUND IN {len(issues_found)} BRANCH(ES):\n")
        for item in issues_found:
            print(f"📍 {item['branch']}:")
            for issue in item['issues']:
                print(f"   • {issue}")
            print()
        
        print("🔧 TO FIX THESE ISSUES:")
        print("   1. Run: python fix_remaining_month_close_issues.py")
        print("      (This will reset savings balances)")
        print()
        print("   2. Run: python reset_security_deposits_after_month_close.py")
        print("      (This will create security return transactions)")
        print()
        print("   3. For vault balances, check if there are legitimate transactions")
        print("      after month closing that explain the balance")
    else:
        print("\n✅ ALL BRANCHES ARE CLEAN!")
        print("   All vaults, savings, and security deposits are at K0.00")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
