#!/usr/bin/env python
"""
Reset security deposits to K0.00 after month closing by creating security return transactions.
This script creates vault transactions to return all security deposits, bringing the balance to K0.00.
EXCLUDES transactions made today to avoid affecting current operations.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from clients.models import Branch
from expenses.models import VaultTransaction
from accounts.models import User
from datetime import datetime, timedelta
import uuid

def main():
    print("=" * 80)
    print("RESETTING SECURITY DEPOSITS AFTER MONTH CLOSING")
    print("=" * 80)
    print("\n⚠️  WARNING: This will create security_return transactions to zero out all security balances")
    print("⚠️  This should only be run AFTER month closing when you want to start fresh")
    print("ℹ️  NOTE: Transactions made TODAY will NOT be affected")
    
    # Get today's date range
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    print(f"\nℹ️  Excluding transactions from: {today_start.strftime('%Y-%m-%d %H:%M:%S')} onwards")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    # Get admin user for recording transactions
    admin_user = User.objects.filter(role='admin', is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.filter(role='admin').first()
    
    if not admin_user:
        print("❌ ERROR: No admin user found to record transactions")
        return
    
    print(f"\n✅ Using admin user: {admin_user.get_full_name()} ({admin_user.username})")
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    total_returned = Decimal('0.00')
    
    for branch in branches:
        print(f"\n{'=' * 80}")
        print(f"BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        # Calculate current security balance from vault transactions BEFORE today
        security_in = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type='security_deposit',
            direction='in',
            transaction_date__lt=today_start  # EXCLUDE today's transactions
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        security_out = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type__in=['security_return', 'security_used'],
            direction='out',
            transaction_date__lt=today_start  # EXCLUDE today's transactions
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Also check today's transactions for reporting
        security_in_today = VaultTransaction.objects.filter(
            branch__iexact=branch.name,
            transaction_type='security_deposit',
            direction='in',
            transaction_date__gte=today_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        security_balance = security_in - security_out
        
        print(f"Security IN (before today): K{security_in:,.2f}")
        print(f"Security OUT (before today): K{security_out:,.2f}")
        print(f"Security IN (today): K{security_in_today:,.2f} [WILL NOT BE TOUCHED]")
        print(f"Balance to Reset: K{security_balance:,.2f}")
        
        if security_balance <= 0:
            print("✅ Security balance is already K0.00 or negative - skipping")
            continue
        
        print(f"\n🔧 Creating security return transaction for K{security_balance:,.2f}...")
        
        # Get current vault balance (we'll use weekly vault for this)
        from loans.models import WeeklyVault
        vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
        
        # Create security return transaction (OUT - returns security to clients)
        VaultTransaction.objects.create(
            branch=branch.name,
            vault_type='weekly',
            transaction_type='security_return',
            direction='out',
            amount=security_balance,
            balance_after=vault.balance - security_balance,
            description=f'Month closing security reset - returning all security deposits to K0.00',
            reference_number=f'SEC-RESET-{uuid.uuid4().hex[:8].upper()}',
            recorded_by=admin_user,
            approved_by=admin_user,
            transaction_date=timezone.now(),
        )
        
        # Update vault balance
        vault.balance -= security_balance
        vault.total_outflows += security_balance
        vault.save()
        
        print(f"✅ Created security return transaction: K{security_balance:,.2f}")
        print(f"✅ Updated vault balance: K{vault.balance:,.2f}")
        
        total_returned += security_balance
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Total security deposits returned: K{total_returned:,.2f}")
    print("✅ All security balances should now be K0.00")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
