#!/usr/bin/env python
"""
Check Vault Date Filtering
===========================
Diagnostic script to check if vault transactions exist and if date filtering works.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from clients.models import Branch
from django.utils import timezone
from datetime import datetime, timedelta

def main():
    print("=" * 80)
    print("VAULT FILTERING DIAGNOSTIC")
    print("=" * 80)
    
    # Check all branches
    branches = Branch.objects.filter(is_active=True)
    print(f"\nActive Branches: {branches.count()}")
    for branch in branches:
        print(f"  - {branch.name}")
    
    print("\n" + "-" * 80)
    print("VAULT TRANSACTIONS BY BRANCH")
    print("-" * 80)
    
    for branch in branches:
        txs = VaultTransaction.objects.filter(branch=branch.name)
        print(f"\n{branch.name}:")
        print(f"  Total transactions: {txs.count()}")
        
        if txs.exists():
            # Show date range
            first_tx = txs.order_by('transaction_date').first()
            last_tx = txs.order_by('-transaction_date').first()
            print(f"  Date range: {first_tx.transaction_date.date()} to {last_tx.transaction_date.date()}")
            
            # Show by type
            from django.db.models import Count
            by_type = txs.values('transaction_type').annotate(count=Count('id')).order_by('-count')
            print(f"  By type:")
            for item in by_type[:5]:
                print(f"    - {item['transaction_type']}: {item['count']}")
            
            # Show by vault type
            by_vault = txs.values('vault_type').annotate(count=Count('id'))
            print(f"  By vault:")
            for item in by_vault:
                vault_name = item['vault_type'] or 'None'
                print(f"    - {vault_name}: {item['count']}")
            
            # Test date filtering
            print(f"\n  Testing date filters:")
            today = timezone.now().date()
            last_week = today - timedelta(days=7)
            last_month = today - timedelta(days=30)
            
            recent = txs.filter(transaction_date__date__gte=last_week).count()
            print(f"    - Last 7 days: {recent}")
            
            month = txs.filter(transaction_date__date__gte=last_month).count()
            print(f"    - Last 30 days: {month}")
            
            # Show sample transactions
            print(f"\n  Sample transactions (last 5):")
            for tx in txs.order_by('-transaction_date')[:5]:
                print(f"    - {tx.transaction_date.date()} | {tx.transaction_type} | {tx.vault_type} | {tx.direction} | K{tx.amount}")
    
    print("\n" + "=" * 80)
    print("CHECKING FOR ISSUES")
    print("=" * 80)
    
    # Check for transactions with NULL transaction_date
    null_dates = VaultTransaction.objects.filter(transaction_date__isnull=True).count()
    if null_dates > 0:
        print(f"\n⚠ WARNING: {null_dates} transactions have NULL transaction_date!")
        print("  These transactions won't appear in date-filtered results.")
    
    # Check for transactions with NULL vault_type
    null_vault = VaultTransaction.objects.filter(vault_type__isnull=True).count()
    if null_vault > 0:
        print(f"\n⚠ WARNING: {null_vault} transactions have NULL vault_type!")
        print("  These transactions won't appear when filtering by vault type.")
    
    # Check for branch name mismatches
    print("\n" + "-" * 80)
    print("BRANCH NAME CONSISTENCY CHECK")
    print("-" * 80)
    
    branch_names_in_db = Branch.objects.values_list('name', flat=True)
    branch_names_in_txs = VaultTransaction.objects.values_list('branch', flat=True).distinct()
    
    print(f"\nBranch names in Branch table: {list(branch_names_in_db)}")
    print(f"Branch names in VaultTransaction: {list(branch_names_in_txs)}")
    
    # Find mismatches
    for tx_branch in branch_names_in_txs:
        if tx_branch not in branch_names_in_db:
            count = VaultTransaction.objects.filter(branch=tx_branch).count()
            print(f"\n⚠ WARNING: {count} transactions reference non-existent branch: '{tx_branch}'")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
