#!/usr/bin/env python
"""
Clean up MANDEVU BRANCJ vault - remove all incorrect transactions.
This will reset the vault to a clean state.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from loans.models import DailyVault, WeeklyVault
from clients.models import Branch
from django.db import transaction as db_transaction

print("=" * 80)
print("MANDEVU BRANCH VAULT CLEANUP")
print("=" * 80)

# Get the branch
branch = Branch.objects.filter(name__icontains='MANDEVU').first()

if not branch:
    print("\n❌ MANDEVU branch not found!")
    exit(1)

print(f"\nBranch: {branch.name}")

# Get all vault transactions for this branch
all_txs = VaultTransaction.objects.filter(branch__iexact=branch.name).order_by('transaction_date')

print(f"\nTotal transactions: {all_txs.count()}")

if all_txs.count() == 0:
    print("\n✅ No transactions to clean up!")
    exit(0)

# Show summary
from decimal import Decimal
from django.db.models import Sum

total_in = all_txs.filter(direction='in').aggregate(total=Sum('amount'))['total'] or Decimal('0')
total_out = all_txs.filter(direction='out').aggregate(total=Sum('amount'))['total'] or Decimal('0')

print(f"\nCurrent state:")
print(f"  Total IN:  K{total_in:,.2f}")
print(f"  Total OUT: K{total_out:,.2f}")
print(f"  Net:       K{(total_in - total_out):,.2f}")

# Get vault balances
daily_vault = DailyVault.objects.filter(branch=branch).first()
weekly_vault = WeeklyVault.objects.filter(branch=branch).first()

if daily_vault:
    print(f"\nDaily Vault Balance:  K{daily_vault.balance:,.2f}")
if weekly_vault:
    print(f"Weekly Vault Balance: K{weekly_vault.balance:,.2f}")

print("\n" + "=" * 80)
print("⚠️  WARNING: This will DELETE ALL transactions for MANDEVU branch!")
print("=" * 80)

response = input("\nAre you sure you want to proceed? Type 'YES' to confirm: ")

if response != 'YES':
    print("\n❌ Cleanup cancelled.")
    exit(0)

print("\n🗑️  Deleting transactions...")

try:
    with db_transaction.atomic():
        # Delete all transactions
        deleted_count = all_txs.count()
        all_txs.delete()
        
        # Reset vault balances to zero
        if daily_vault:
            daily_vault.balance = Decimal('0')
            daily_vault.total_inflows = Decimal('0')
            daily_vault.total_outflows = Decimal('0')
            daily_vault.save()
            print(f"✅ Daily vault reset to K0.00")
        
        if weekly_vault:
            weekly_vault.balance = Decimal('0')
            weekly_vault.total_inflows = Decimal('0')
            weekly_vault.total_outflows = Decimal('0')
            weekly_vault.save()
            print(f"✅ Weekly vault reset to K0.00")
        
        print(f"\n✅ Successfully deleted {deleted_count} transactions!")
        print(f"✅ Vault balances reset to K0.00")
        
except Exception as e:
    print(f"\n❌ Error during cleanup: {e}")
    exit(1)

print("\n" + "=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
print("\nNext steps:")
print("1. Record any capital injection if needed")
print("2. Record transactions correctly going forward")
print("3. Payment collections should be IN (▲)")
print("4. Disbursements should be OUT (▼)")
print("\n" + "=" * 80)
