#!/usr/bin/env python
"""
Fix MANDEVU branch negative balance by injecting K25 capital.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.utils import timezone
from decimal import Decimal
from clients.models import Branch
from loans.models import WeeklyVault
from expenses.models import VaultTransaction
from accounts.models import User
import uuid

def main():
    print("=" * 80)
    print("FIXING MANDEVU NEGATIVE BALANCE")
    print("=" * 80)
    
    # Get admin user
    admin_user = User.objects.filter(role='admin', is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.filter(role='admin').first()
    
    if not admin_user:
        print("❌ ERROR: No admin user found")
        return
    
    print(f"✅ Using admin user: {admin_user.get_full_name()}\n")
    
    # Get MANDEVU branch
    try:
        branch = Branch.objects.get(name__iexact='MANDEVU')
    except Branch.DoesNotExist:
        print("❌ ERROR: MANDEVU branch not found")
        return
    
    print(f"Branch: {branch.name}")
    
    # Get weekly vault
    weekly_vault, _ = WeeklyVault.objects.get_or_create(branch=branch)
    
    print(f"Current Weekly Vault Balance: K{weekly_vault.balance:,.2f}")
    
    if weekly_vault.balance >= 0:
        print("✅ Vault balance is already positive or zero - no fix needed")
        return
    
    # Calculate amount needed
    amount_needed = abs(weekly_vault.balance)
    print(f"\n🔧 Injecting K{amount_needed:,.2f} capital...")
    
    # Create capital injection transaction
    VaultTransaction.objects.create(
        branch=branch.name,
        vault_type='weekly',
        transaction_type='capital_injection',
        direction='in',
        amount=amount_needed,
        balance_after=Decimal('0.00'),
        description=f'Capital injection to fix negative balance caused by bank charges',
        reference_number=f'FIX-MANDEVU-{uuid.uuid4().hex[:8].upper()}',
        recorded_by=admin_user,
        approved_by=admin_user,
        transaction_date=timezone.now(),
    )
    
    # Update vault balance
    weekly_vault.balance = Decimal('0.00')
    weekly_vault.total_inflows += amount_needed
    weekly_vault.save()
    
    print(f"✅ Capital injection created: K{amount_needed:,.2f}")
    print(f"✅ New vault balance: K{weekly_vault.balance:,.2f}")
    
    print("\n" + "=" * 80)
    print("FIX COMPLETE")
    print("=" * 80)
    print("\n⚠️  IMPORTANT: Users should hard refresh their browser (Ctrl+Shift+R)")

if __name__ == '__main__':
    main()
