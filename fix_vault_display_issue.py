#!/usr/bin/env python
"""
Fix vault display issues by checking and correcting branch name mismatches
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from expenses.models import VaultTransaction
from clients.models import Branch
from accounts.models import User

print("\n" + "="*60)
print("VAULT DISPLAY ISSUE FIX")
print("="*60)

# Step 1: Check for branch name mismatches
print("\n📋 Step 1: Checking branch name consistency...")

branches = Branch.objects.filter(is_active=True)
vault_branches = VaultTransaction.objects.values_list('branch', flat=True).distinct()

print(f"\nBranches in Branch model: {branches.count()}")
for b in branches:
    print(f"   - '{b.name}'")

print(f"\nBranch names in VaultTransaction: {len(vault_branches)}")
for vb in vault_branches:
    print(f"   - '{vb}'")

# Step 2: Find mismatches
print("\n🔍 Step 2: Finding mismatches...")
mismatches = []
for vb in vault_branches:
    # Check if this vault branch name matches any Branch model name
    exact_match = branches.filter(name=vb).exists()
    if not exact_match:
        # Try case-insensitive
        case_match = branches.filter(name__iexact=vb).first()
        if case_match:
            mismatches.append({
                'vault_name': vb,
                'branch_name': case_match.name,
                'type': 'case_mismatch'
            })
        else:
            # Try contains
            contains_match = branches.filter(name__icontains=vb).first()
            if contains_match:
                mismatches.append({
                    'vault_name': vb,
                    'branch_name': contains_match.name,
                    'type': 'partial_match'
                })
            else:
                mismatches.append({
                    'vault_name': vb,
                    'branch_name': None,
                    'type': 'no_match'
                })

if mismatches:
    print(f"\n⚠️  Found {len(mismatches)} mismatch(es):")
    for m in mismatches:
        print(f"\n   Vault Transaction branch: '{m['vault_name']}'")
        if m['branch_name']:
            print(f"   Branch model name: '{m['branch_name']}'")
            print(f"   Type: {m['type']}")
            count = VaultTransaction.objects.filter(branch=m['vault_name']).count()
            print(f"   Affected transactions: {count}")
        else:
            print(f"   ❌ No matching branch found in Branch model!")
            count = VaultTransaction.objects.filter(branch=m['vault_name']).count()
            print(f"   Orphaned transactions: {count}")
else:
    print("\n✅ No mismatches found - all branch names match!")

# Step 3: Check manager access
print("\n\n👤 Step 3: Checking manager access...")
managers = User.objects.filter(role='manager', is_active=True)

for manager in managers:
    print(f"\nManager: {manager.get_full_name()}")
    try:
        branch = manager.managed_branch
        print(f"   Branch: '{branch.name}'")
        
        # Count transactions
        tx_count = VaultTransaction.objects.filter(branch=branch.name).count()
        print(f"   Transactions (exact match): {tx_count}")
        
        if tx_count == 0:
            # Try case-insensitive
            tx_count_ci = VaultTransaction.objects.filter(branch__iexact=branch.name).count()
            print(f"   Transactions (case-insensitive): {tx_count_ci}")
            
            if tx_count_ci > 0:
                print(f"   ⚠️  ISSUE: Branch name case mismatch!")
                print(f"   Manager's branch: '{branch.name}'")
                vault_name = VaultTransaction.objects.filter(
                    branch__iexact=branch.name
                ).first().branch
                print(f"   Vault transactions use: '{vault_name}'")
    except Exception as e:
        print(f"   ❌ No branch assigned: {e}")

# Step 4: Recommendations
print("\n\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)

if mismatches:
    print("\n⚠️  ACTION REQUIRED:")
    print("\nOption 1: Update VaultTransaction records to match Branch names")
    print("Option 2: Use case-insensitive filtering in vault query")
    print("\nTo fix automatically, we can update the vault_views.py to use")
    print("case-insensitive filtering: .filter(branch__iexact=branch_name)")
else:
    print("\n✅ No action needed - branch names are consistent!")
    print("\nIf vault still shows 'No transactions', check:")
    print("1. User is logged in as manager with assigned branch")
    print("2. Browser cache is cleared")
    print("3. Development server is restarted")

print("\n" + "="*60 + "\n")
