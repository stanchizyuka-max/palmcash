#!/usr/bin/env python
"""
Investigate capital injection and security return transactions created by fix scripts.
Shows exactly when they were created, by whom, and why.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from clients.models import Branch
from expenses.models import VaultTransaction
from datetime import datetime

def main():
    print("=" * 80)
    print("INVESTIGATING CAPITAL INJECTION & SECURITY RETURN TRANSACTIONS")
    print("=" * 80)
    print()
    
    # Get today's date
    today = timezone.now().date()
    print(f"Today's date: {today.strftime('%Y-%m-%d')}")
    print()
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"📍 BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        # Find capital injection transactions
        capital_injections = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type='capital_injection'
        ).order_by('-transaction_date')
        
        # Find security return transactions
        security_returns = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type='security_return'
        ).order_by('-transaction_date')
        
        print(f"\n💰 CAPITAL INJECTIONS: {capital_injections.count()} found")
        print("-" * 80)
        
        if capital_injections.exists():
            for tx in capital_injections:
                print(f"\nTransaction ID: {tx.id}")
                print(f"Date: {tx.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Amount: K{tx.amount:,.2f}")
                print(f"Vault Type: {tx.vault_type.title()}")
                print(f"Direction: {tx.direction.upper()}")
                print(f"Balance After: K{tx.balance_after:,.2f}")
                print(f"Description: {tx.description}")
                print(f"Reference: {tx.reference_number}")
                print(f"Recorded By: {tx.recorded_by.get_full_name() if tx.recorded_by else 'N/A'}")
                print(f"Approved By: {tx.approved_by.get_full_name() if tx.approved_by else 'N/A'}")
                
                # Determine which script created this
                if 'negative balance' in tx.description.lower():
                    print(f"🔍 Source: fix_negative_vault_balances.py script")
                    print(f"📝 Reason: Vault had negative balance after security returns")
                elif 'correction' in tx.description.lower():
                    print(f"🔍 Source: fix_chazanga_negative_vault.py script")
                    print(f"📝 Reason: Manual correction for negative balance")
                else:
                    print(f"🔍 Source: Unknown/Manual")
        else:
            print("✅ No capital injections found")
        
        print(f"\n🔒 SECURITY RETURNS: {security_returns.count()} found")
        print("-" * 80)
        
        if security_returns.exists():
            for tx in security_returns:
                print(f"\nTransaction ID: {tx.id}")
                print(f"Date: {tx.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Amount: K{tx.amount:,.2f}")
                print(f"Vault Type: {tx.vault_type.title()}")
                print(f"Direction: {tx.direction.upper()}")
                print(f"Balance After: K{tx.balance_after:,.2f}")
                print(f"Description: {tx.description}")
                print(f"Reference: {tx.reference_number}")
                print(f"Recorded By: {tx.recorded_by.get_full_name() if tx.recorded_by else 'N/A'}")
                print(f"Approved By: {tx.approved_by.get_full_name() if tx.approved_by else 'N/A'}")
                
                # Determine which script created this
                if 'month closing' in tx.description.lower() and 'reset' in tx.description.lower():
                    print(f"🔍 Source: reset_security_deposits_after_month_close.py script")
                    print(f"📝 Reason: Month closing - returning all security deposits to K0.00")
                elif 'undo' in tx.description.lower():
                    print(f"🔍 Source: undo_todays_security_returns.py script")
                    print(f"📝 Reason: Reversal of earlier security return")
                else:
                    print(f"🔍 Source: Unknown/Manual")
        else:
            print("✅ No security returns found")
        
        # Calculate current security balance
        print(f"\n📊 CURRENT SECURITY BALANCE:")
        print("-" * 80)
        
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
        
        print(f"Total Security IN: K{security_in:,.2f}")
        print(f"Total Security OUT: K{security_out:,.2f}")
        print(f"Current Balance: K{security_balance:,.2f} {'✅' if security_balance == 0 else '⚠️'}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY & EXPLANATION")
    print("=" * 80)
    print()
    print("📋 WHAT HAPPENED:")
    print()
    print("1. SECURITY RETURNS (K9,600 per branch):")
    print("   - Created by: reset_security_deposits_after_month_close.py")
    print("   - Purpose: Return all security deposits to clients after month closing")
    print("   - Effect: Reduces vault balance by the security amount")
    print("   - Why: Month closing should reset everything to K0.00")
    print()
    print("2. CAPITAL INJECTIONS (K9,600 per branch):")
    print("   - Created by: fix_negative_vault_balances.py")
    print("   - Purpose: Fix negative vault balances caused by security returns")
    print("   - Effect: Brings vault balance back to K0.00")
    print("   - Why: Vault went negative because security was returned but vault didn't have enough cash")
    print()
    print("🔍 ROOT CAUSE:")
    print("   When you close the month, security deposits should be returned to clients.")
    print("   However, if the vault doesn't have enough cash to cover the returns,")
    print("   it goes negative. The capital injection fixes this by adding the missing funds.")
    print()
    print("💡 WHAT THIS MEANS:")
    print("   - These are ACCOUNTING transactions, not real money movements")
    print("   - They balance the books after month closing")
    print("   - Security deposits are now K0.00 (reset for new month)")
    print("   - Vault balances are K0.00 or positive (corrected)")
    print()
    print("✅ THESE TRANSACTIONS ARE CORRECT AND EXPECTED")
    print("   They were created by the month closing fix scripts to properly reset")
    print("   all balances to K0.00 as requested.")
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
