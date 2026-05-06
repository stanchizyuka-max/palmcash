#!/usr/bin/env python
"""
Fix Mandevu Branch Name Change
================================
This script updates all database references from "MANDEVU BRANCJ" to "MANDEVU BRANCH"
after the branch name was corrected.

It updates:
- VaultTransaction records (branch field)
- User assignments (managed_branch)
- Loan records (branch field if exists)
- Any other tables that reference the branch by name
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import transaction
from clients.models import Branch
from expenses.models import VaultTransaction
from accounts.models import User

OLD_NAME = "MANDEVU BRANCJ"
NEW_NAME = "MANDEVU BRANCH"

def main():
    print("=" * 80)
    print("MANDEVU BRANCH NAME FIX")
    print("=" * 80)
    print(f"Updating all references from '{OLD_NAME}' to '{NEW_NAME}'")
    print()
    
    # Check if the new branch exists
    try:
        new_branch = Branch.objects.get(name=NEW_NAME)
        print(f"✓ Found new branch: {new_branch.name} (ID: {new_branch.id})")
    except Branch.DoesNotExist:
        print(f"✗ ERROR: Branch '{NEW_NAME}' not found!")
        print("Please make sure you've renamed the branch in the admin panel first.")
        return
    
    # Check if old branch still exists
    old_branch_exists = Branch.objects.filter(name=OLD_NAME).exists()
    if old_branch_exists:
        print(f"⚠ WARNING: Old branch '{OLD_NAME}' still exists!")
        print("You may want to delete it after this script completes.")
    
    print()
    print("-" * 80)
    print("STARTING DATABASE UPDATES...")
    print("-" * 80)
    
    with transaction.atomic():
        # 1. Update VaultTransaction records
        vault_txs = VaultTransaction.objects.filter(branch=OLD_NAME)
        vault_count = vault_txs.count()
        print(f"\n1. VaultTransaction records: {vault_count} found")
        if vault_count > 0:
            vault_txs.update(branch=NEW_NAME)
            print(f"   ✓ Updated {vault_count} vault transactions")
        
        # 2. Update User managed_branch (for managers)
        from django.contrib.contenttypes.models import ContentType
        from django.db.models import Q
        
        managers = User.objects.filter(
            role='manager',
            managed_branch__name=OLD_NAME
        )
        manager_count = managers.count()
        print(f"\n2. Manager assignments: {manager_count} found")
        if manager_count > 0:
            for manager in managers:
                manager.managed_branch = new_branch
                manager.save(update_fields=['managed_branch'])
            print(f"   ✓ Updated {manager_count} manager assignments")
        
        # 3. Update Loan records if they have a branch field
        try:
            from loans.models import Loan
            # Check if Loan model has a branch field
            if hasattr(Loan, 'branch'):
                loans = Loan.objects.filter(branch__name=OLD_NAME)
                loan_count = loans.count()
                print(f"\n3. Loan records: {loan_count} found")
                if loan_count > 0:
                    loans.update(branch=new_branch)
                    print(f"   ✓ Updated {loan_count} loan records")
            else:
                print(f"\n3. Loan records: No branch field (skipping)")
        except Exception as e:
            print(f"\n3. Loan records: Error - {e}")
        
        # 4. Update BorrowerGroup records
        try:
            from clients.models import BorrowerGroup
            groups = BorrowerGroup.objects.filter(branch__name=OLD_NAME)
            group_count = groups.count()
            print(f"\n4. BorrowerGroup records: {group_count} found")
            if group_count > 0:
                groups.update(branch=new_branch)
                print(f"   ✓ Updated {group_count} borrower groups")
        except Exception as e:
            print(f"\n4. BorrowerGroup records: Error - {e}")
        
        # 5. Update DailyVault and WeeklyVault
        try:
            from loans.models import DailyVault, WeeklyVault
            
            daily_vaults = DailyVault.objects.filter(branch__name=OLD_NAME)
            daily_count = daily_vaults.count()
            print(f"\n5. DailyVault records: {daily_count} found")
            if daily_count > 0:
                daily_vaults.update(branch=new_branch)
                print(f"   ✓ Updated {daily_count} daily vault records")
            
            weekly_vaults = WeeklyVault.objects.filter(branch__name=OLD_NAME)
            weekly_count = weekly_vaults.count()
            print(f"\n6. WeeklyVault records: {weekly_count} found")
            if weekly_count > 0:
                weekly_vaults.update(branch=new_branch)
                print(f"   ✓ Updated {weekly_count} weekly vault records")
        except Exception as e:
            print(f"\n5-6. Vault records: Error - {e}")
        
        # 7. Update BranchSavings
        try:
            from loans.models import BranchSavings
            savings = BranchSavings.objects.filter(branch__name=OLD_NAME)
            savings_count = savings.count()
            print(f"\n7. BranchSavings records: {savings_count} found")
            if savings_count > 0:
                savings.update(branch=new_branch)
                print(f"   ✓ Updated {savings_count} branch savings records")
        except Exception as e:
            print(f"\n7. BranchSavings records: Error - {e}")
        
        # 8. Update OfficerAssignment
        try:
            from clients.models import OfficerAssignment
            assignments = OfficerAssignment.objects.filter(branch__name=OLD_NAME)
            assignment_count = assignments.count()
            print(f"\n8. OfficerAssignment records: {assignment_count} found")
            if assignment_count > 0:
                assignments.update(branch=new_branch)
                print(f"   ✓ Updated {assignment_count} officer assignments")
        except Exception as e:
            print(f"\n8. OfficerAssignment records: Error - {e}")
    
    print()
    print("-" * 80)
    print("VERIFICATION")
    print("-" * 80)
    
    # Verify the changes
    remaining_old = VaultTransaction.objects.filter(branch=OLD_NAME).count()
    new_count = VaultTransaction.objects.filter(branch=NEW_NAME).count()
    
    print(f"\nVaultTransaction records:")
    print(f"  - Old name ('{OLD_NAME}'): {remaining_old}")
    print(f"  - New name ('{NEW_NAME}'): {new_count}")
    
    if remaining_old == 0:
        print("\n✓ SUCCESS! All records have been updated.")
        print(f"\nThe branch '{NEW_NAME}' now has all its historical data restored.")
    else:
        print(f"\n⚠ WARNING: {remaining_old} records still reference the old name.")
    
    print()
    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Check the vault transactions for MANDEVU BRANCH")
    print("2. Verify officer assignments are showing correctly")
    print("3. If everything looks good, you can delete the old branch if it still exists")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
