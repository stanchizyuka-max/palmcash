#!/usr/bin/env python
"""
Diagnose why vault page shows no transactions when database has them
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from clients.models import Branch
from accounts.models import User

print("\n" + "="*60)
print("VAULT FILTER DIAGNOSIS")
print("="*60)

# Get manager users
managers = User.objects.filter(role='manager', is_active=True)
print(f"\n👤 Active Managers: {managers.count()}")

for manager in managers:
    print(f"\n   Manager: {manager.get_full_name()}")
    
    # Check if manager has a branch
    try:
        branch = manager.managed_branch
        print(f"   ✅ Has branch: '{branch.name}'")
        print(f"      Branch ID: {branch.id}")
        
        # Check transactions for this branch (exact match)
        exact_match = VaultTransaction.objects.filter(branch=branch.name)
        print(f"      Transactions (exact match): {exact_match.count()}")
        
        # Check transactions with case-insensitive match
        case_insensitive = VaultTransaction.objects.filter(branch__iexact=branch.name)
        print(f"      Transactions (case-insensitive): {case_insensitive.count()}")
        
        # Check transactions containing branch name
        contains = VaultTransaction.objects.filter(branch__icontains=branch.name)
        print(f"      Transactions (contains): {contains.count()}")
        
        # Show actual branch names in transactions
        unique_branches = VaultTransaction.objects.values_list('branch', flat=True).distinct()
        print(f"\n   📋 All branch names in VaultTransaction:")
        for b in unique_branches:
            count = VaultTransaction.objects.filter(branch=b).count()
            print(f"      '{b}' ({count} transactions)")
            
    except Exception as e:
        print(f"   ❌ No branch assigned: {e}")

# Check admin users
admins = User.objects.filter(role='admin', is_active=True)
print(f"\n\n👑 Active Admins: {admins.count()}")
for admin in admins:
    print(f"   {admin.get_full_name()}")

# Show all branches
print(f"\n\n🏢 All Active Branches:")
branches = Branch.objects.filter(is_active=True)
for branch in branches:
    print(f"   ID: {branch.id} | Name: '{branch.name}'")
    exact = VaultTransaction.objects.filter(branch=branch.name).count()
    print(f"      Transactions: {exact}")

print("\n" + "="*60)
print("DIAGNOSIS COMPLETE")
print("="*60)

# Recommendations
print("\n💡 RECOMMENDATIONS:")
print("\nIf a manager's branch has 0 transactions (exact match) but")
print("transactions exist with similar names, the issue is:")
print("1. Branch name mismatch between Branch model and VaultTransaction")
print("2. Extra spaces or different capitalization")
print("3. Branch was renamed but old transactions have old name")
print("\nSOLUTION: Update VaultTransaction records to match current branch names")
print("or use case-insensitive filtering in the vault query.\n")
