#!/usr/bin/env python
"""
Fix negative vault balances caused by security returns.
Injects capital to bring negative balances back to K0.00.
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
from accounts.models import User
import uuid

def main():
    print("=" * 80)
    print("FIXING NEGATIVE VAULT BALANCES")
    print("=" * 80)
    
    # Get admin user
    admin_user = User.objects.filter(role='admin', is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.filter(role='admin').first()
    
    if not admin_user:
        print("❌ ERROR: No admin user found")
        return
    
    print(f"✅ Using admin user: {admin_user.get_full_name()}\n")
    
    branches = Branch.objects.filter(is_active=True).order_by('name')
    total_injected = Decimal('0.00')
    
    for branch in branches:
        print(f"{'=' * 80}")
        print(f"BRANCH: {branch.name}")
        print(f"{'=' * 80}")
        
        daily_vault, _ = DailyVault.objects.get_or_create(branch=branch)
        weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
        
        print(f"Daily Vault Balance: K{daily_vault.balance:,.2f}")
        print(f"Weekly Vault Balance: K{weekly_vault.balance:,.2f}")
        
        # Fix daily vault if negative
        if daily_vault.balance < 0:
            amount = abs(daily_vault.balance)
            print(f"\n🔧 Injecting K{amount:,.2f} into Daily Vault...")
            
            VaultTransaction.objects.create(
                branch=branch.name,
                vault_type='daily',
                transaction_type='capital_injection',
                direction='in',
                amount=amount,
                balance_after=Decimal('0.00'),
                description=f'Capital injection to fix negative balance after security returns',
                reference_number=f'FIX-DAILY-{uuid.uuid4().hex[:8].upper()}',
                recorded_by=admin_user,
                approved_by=admin_user,
                transaction_date=timezone.now(),
            )
            
            daily_vault.balance = Decimal('0.00')
            daily_vault.total_inflows += amount
            daily_vault.save()
            
            print(f"✅ Daily Vault fixed: K{amount:,.2f} injected")
            total_injected += amount
        else:
            print(f"✅ Daily Vault is OK")
        
        # Fix weekly vault if negative
        if weekly_vault.balance < 0:
            amount = abs(weekly_vault.balance)
            print(f"\n🔧 Injecting K{amount:,.2f} into Weekly Vault...")
            
            VaultTransaction.objects.create(
                branch=branch.name,
                vault_type='weekly',
                transaction_type='capital_injection',
                direction='in',
                amount=amount,
                balance_after=Decimal('0.00'),
                description=f'Capital injection to fix negative balance after security returns',
                reference_number=f'FIX-WEEKLY-{uuid.uuid4().hex[:8].upper()}',
                recorded_by=admin_user,
                approved_by=admin_user,
                transaction_date=timezone.now(),
            )
            
            weekly_vault.balance = Decimal('0.00')
            weekly_vault.total_inflows += amount
            weekly_vault.save()
            
            print(f"✅ Weekly Vault fixed: K{amount:,.2f} injected")
            total_injected += amount
        else:
            print(f"✅ Weekly Vault is OK")
        
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Total capital injected: K{total_injected:,.2f}")
    print("✅ All vault balances should now be K0.00 or positive")
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")
    print("=" * 80)

if __name__ == '__main__':
    main()
