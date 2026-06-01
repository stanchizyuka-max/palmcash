#!/usr/bin/env python
"""
Recalculate vault inflows/outflows based on transactions AFTER the last month closing.
This resets the counters to show only current month activity, not cumulative totals.

The script:
1. Finds the last month closing date for each branch
2. Calculates inflows/outflows from transactions AFTER that date
3. Updates the vault totals to reflect only current month activity
4. Keeps all transactions intact - only updates the counters
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')

# Try to load .env if it exists
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / 'palmcash' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

django.setup()

from loans.models import DailyVault, WeeklyVault
from expenses.models import VaultTransaction
from clients.models import Branch
from django.db.models import Sum
from decimal import Decimal

print("=" * 70)
print("RECALCULATE VAULT TOTALS AFTER MONTH CLOSING")
print("=" * 70)

print("\nThis script will:")
print("1. Find the last month closing date for each branch")
print("2. Calculate inflows/outflows from transactions AFTER that date")
print("3. Update vault totals to show only current month activity")
print("4. Keep all transactions intact")

# Get all branches
branches = Branch.objects.filter(is_active=True).order_by('name')

print(f"\n📊 Processing {branches.count()} branches...")
print("=" * 70)

for branch in branches:
    print(f"\n🏢 Branch: {branch.name}")
    print("-" * 70)
    
    # Find the last month closing date for this branch
    last_closing = VaultTransaction.objects.filter(
        branch=branch.name,
        transaction_type='month_close'
    ).order_by('-transaction_date').first()
    
    if last_closing:
        closing_date = last_closing.transaction_date
        print(f"   Last month closed: {closing_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Recalculating from transactions AFTER this date...")
    else:
        closing_date = None
        print(f"   ⚠️  No month closing found - will calculate from ALL transactions")
    
    # Process Daily Vault
    try:
        daily_vault = DailyVault.objects.get(branch=branch)
        
        # Get transactions after last closing
        if closing_date:
            daily_txns = VaultTransaction.objects.filter(
                branch=branch.name,
                vault_type='daily',
                transaction_date__gt=closing_date
            ).exclude(transaction_type='month_close')
        else:
            daily_txns = VaultTransaction.objects.filter(
                branch=branch.name,
                vault_type='daily'
            ).exclude(transaction_type='month_close')
        
        # Calculate inflows and outflows
        daily_inflows = daily_txns.filter(direction='in').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        daily_outflows = daily_txns.filter(direction='out').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        
        # Show before/after
        print(f"\n   📅 Daily Vault:")
        print(f"      Before: Inflows K{daily_vault.total_inflows:,.2f}, Outflows K{daily_vault.total_outflows:,.2f}")
        print(f"      After:  Inflows K{daily_inflows:,.2f}, Outflows K{daily_outflows:,.2f}")
        
        # Update vault
        daily_vault.total_inflows = daily_inflows
        daily_vault.total_outflows = daily_outflows
        daily_vault.save(update_fields=['total_inflows', 'total_outflows'])
        
        print(f"      ✅ Updated")
        
    except DailyVault.DoesNotExist:
        print(f"   ⏭️  No Daily Vault found")
    
    # Process Weekly Vault
    try:
        weekly_vault = WeeklyVault.objects.get(branch=branch)
        
        # Get transactions after last closing
        if closing_date:
            weekly_txns = VaultTransaction.objects.filter(
                branch=branch.name,
                vault_type='weekly',
                transaction_date__gt=closing_date
            ).exclude(transaction_type='month_close')
        else:
            weekly_txns = VaultTransaction.objects.filter(
                branch=branch.name,
                vault_type='weekly'
            ).exclude(transaction_type='month_close')
        
        # Calculate inflows and outflows
        weekly_inflows = weekly_txns.filter(direction='in').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        weekly_outflows = weekly_txns.filter(direction='out').aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        
        # Show before/after
        print(f"\n   📆 Weekly Vault:")
        print(f"      Before: Inflows K{weekly_vault.total_inflows:,.2f}, Outflows K{weekly_vault.total_outflows:,.2f}")
        print(f"      After:  Inflows K{weekly_inflows:,.2f}, Outflows K{weekly_outflows:,.2f}")
        
        # Update vault
        weekly_vault.total_inflows = weekly_inflows
        weekly_vault.total_outflows = weekly_outflows
        weekly_vault.save(update_fields=['total_inflows', 'total_outflows'])
        
        print(f"      ✅ Updated")
        
    except WeeklyVault.DoesNotExist:
        print(f"   ⏭️  No Weekly Vault found")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

# Show final totals for all branches
print("\nFinal Vault Totals (Current Month Activity):")
print("-" * 70)

for branch in branches:
    try:
        daily = DailyVault.objects.get(branch=branch)
        weekly = WeeklyVault.objects.get(branch=branch)
        
        total_inflows = daily.total_inflows + weekly.total_inflows
        total_outflows = daily.total_outflows + weekly.total_outflows
        
        print(f"\n{branch.name}:")
        print(f"   Daily:  In K{daily.total_inflows:,.2f}, Out K{daily.total_outflows:,.2f}")
        print(f"   Weekly: In K{weekly.total_inflows:,.2f}, Out K{weekly.total_outflows:,.2f}")
        print(f"   TOTAL:  In K{total_inflows:,.2f}, Out K{total_outflows:,.2f}")
    except:
        pass

print("\n" + "=" * 70)
print("✅ COMPLETE")
print("=" * 70)
print("\nVault totals now reflect only transactions AFTER the last month closing.")
print("All transaction records remain intact in the database.")
print("\nRefresh your vault page to see the updated totals!")
