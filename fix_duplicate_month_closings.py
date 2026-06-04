#!/usr/bin/env python
"""
Fix duplicate month closing transactions that are removing opening balances
Found: June 2 transactions that are OUT (removing) instead of bringing forward
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from django.utils import timezone
from datetime import datetime

def fix_duplicates():
    """Delete duplicate month closing OUT transactions from June 2"""
    
    print("=" * 80)
    print("     FIX DUPLICATE MONTH CLOSING TRANSACTIONS")
    print("=" * 80)
    print()
    print("⚠️  This script will DELETE duplicate month closing transactions")
    print("    that are removing opening balances (direction=OUT)")
    print()
    
    june_2 = timezone.make_aware(datetime(2026, 6, 2, 0, 0, 0))
    june_3 = timezone.make_aware(datetime(2026, 6, 3, 0, 0, 0))
    
    # Find duplicate month closing transactions on June 2
    duplicates = VaultTransaction.objects.filter(
        transaction_type='month_close',
        direction='out',  # These are the problematic ones
        transaction_date__gte=june_2,
        transaction_date__lt=june_3
    ).order_by('branch', 'transaction_date')
    
    if not duplicates.exists():
        print("✅ No duplicate month closing OUT transactions found!")
        print("   The issue might have been fixed already.")
        return
    
    print(f"🔍 FOUND {duplicates.count()} DUPLICATE TRANSACTIONS:")
    print()
    
    for tx in duplicates:
        print(f"  TX #{tx.id}")
        print(f"    Branch:      {tx.branch}")
        print(f"    Date:        {tx.transaction_date}")
        print(f"    Vault Type:  {tx.vault_type.upper()}")
        print(f"    Direction:   {tx.direction.upper()} ❌ (should be IN)")
        print(f"    Amount:      K{tx.amount:,.2f}")
        print(f"    Description: {tx.description}")
        print()
    
    print("=" * 80)
    print()
    response = input("Do you want to DELETE these duplicate transactions? (yes/no): ")
    
    if response.lower() != 'yes':
        print("\n❌ Aborted. No changes made.")
        return
    
    print()
    print("🗑️  DELETING DUPLICATES...")
    print()
    
    deleted_count = 0
    for tx in duplicates:
        print(f"  Deleting TX #{tx.id} ({tx.branch} - {tx.vault_type} - K{tx.amount:,.2f})")
        tx.delete()
        deleted_count += 1
    
    print()
    print(f"✅ Deleted {deleted_count} duplicate transaction(s)")
    print()
    print("=" * 80)
    print()
    print("NEXT STEP:")
    print("---------")
    print("Run recalculate_all_vault_balances.py to update vault balances:")
    print()
    print("  python recalculate_all_vault_balances.py")
    print()
    print("This will:")
    print("  • Recalculate balances for all vaults")
    print("  • Fix the discrepancies")
    print("  • Sync vault models with transactions")
    print()
    print("=" * 80)

if __name__ == '__main__':
    fix_duplicates()
