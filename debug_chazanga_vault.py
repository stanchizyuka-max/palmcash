#!/usr/bin/env python
"""
Debug Chazanga Vault Display Issue
===================================
This script diagnoses why vault transactions aren't showing for Chazanga branch
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from clients.models import Branch
from expenses.models import VaultTransaction
from accounts.models import User

def main():
    print("=" * 80)
    print("CHAZANGA VAULT DIAGNOSTIC")
    print("=" * 80)
    
    # Get Chazanga branch
    try:
        chazanga = Branch.objects.get(name='Chazanga')
        print(f"\n✓ Found branch: {chazanga.name} (ID: {chazanga.id})")
    except Branch.DoesNotExist:
        print(f"\n✗ ERROR: Chazanga branch not found!")
        print("\nAvailable branches:")
        for b in Branch.objects.all():
            print(f"  - {b.name}")
        return
    
    print(f"\n" + "-" * 80)
    print("VAULT TRANSACTIONS CHECK")
    print("-" * 80)
    
    # Check transactions by exact name match
    exact_match = VaultTransaction.objects.filter(branch='Chazanga')
    print(f"\nTransactions with branch='Chazanga': {exact_match.count()}")
    
    # Check transactions with case-insensitive match
    case_insensitive = VaultTransaction.objects.filter(branch__iexact='chazanga')
    print(f"Transactions with branch__iexact='chazanga': {case_insensitive.count()}")
    
    # Check all variations
    variations = ['Chazanga', 'CHAZANGA', 'chazanga', 'Chazanga ', ' Chazanga']
    for var in variations:
        count = VaultTransaction.objects.filter(branch=var).count()
        if count > 0:
            print(f"  - '{var}': {count} transactions")
    
    # Show sample transactions
    if exact_match.exists():
        print(f"\nSample transactions (first 5):")
        for tx in exact_match.order_by('-transaction_date')[:5]:
            print(f"  - {tx.transaction_date.date()} | {tx.transaction_type} | {tx.direction} | K{tx.amount}")
    
    print(f"\n" + "-" * 80)
    print("MANAGER CHECK")
    print("-" * 80)
    
    # Check if there's a manager for Chazanga
    managers = User.objects.filter(role='manager', managed_branch=chazanga)
    print(f"\nManagers for Chazanga: {managers.count()}")
    for manager in managers:
        print(f"  - {manager.get_full_name()} ({manager.username})")
    
    # Check all managers
    all_managers = User.objects.filter(role='manager')
    print(f"\nAll managers in system: {all_managers.count()}")
    for manager in all_managers:
        branch_name = manager.managed_branch.name if manager.managed_branch else 'No Branch'
        print(f"  - {manager.get_full_name()} → {branch_name}")
    
    print(f"\n" + "-" * 80)
    print("VAULT VIEW SIMULATION")
    print("-" * 80)
    
    # Simulate what the vault view does
    print(f"\nSimulating vault_dashboard view logic:")
    print(f"  1. Branch name from object: '{chazanga.name}'")
    print(f"  2. Querying: VaultTransaction.objects.filter(branch='{chazanga.name}')")
    
    qs = VaultTransaction.objects.filter(branch=chazanga.name)
    print(f"  3. Result: {qs.count()} transactions")
    
    if qs.count() == 0:
        print(f"\n⚠ ISSUE FOUND: No transactions match branch name '{chazanga.name}'")
        print(f"\nPossible causes:")
        print(f"  1. Branch name has extra spaces or different casing")
        print(f"  2. Transactions were recorded with a different branch name")
        print(f"  3. Branch name was changed after transactions were created")
        
        # Check what branch names exist in transactions
        print(f"\n" + "-" * 80)
        print("BRANCH NAMES IN VAULT TRANSACTIONS")
        print("-" * 80)
        
        from django.db.models import Count
        branch_names = VaultTransaction.objects.values('branch').annotate(
            count=Count('id')
        ).order_by('-count')
        
        print(f"\nUnique branch names in VaultTransaction:")
        for item in branch_names:
            print(f"  - '{item['branch']}': {item['count']} transactions")
            # Check if it's similar to Chazanga
            if 'chazanga' in item['branch'].lower():
                print(f"    ^ This looks like Chazanga!")
    else:
        print(f"\n✓ Transactions found! The vault should be displaying them.")
        print(f"\nIf you still see 'No vault transactions yet', the issue might be:")
        print(f"  1. Browser cache - try hard refresh (Ctrl+Shift+R)")
        print(f"  2. Server not restarted after code changes")
        print(f"  3. Pagination issue - transactions exist but not on first page")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
