#!/usr/bin/env python
"""
Fix MANDEVU BRANCH Groups
==========================
Update groups that are still showing "MANDEVU BRANCJ" to use the correct branch
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import transaction
from clients.models import Branch, BorrowerGroup
from loans.models import Loan

OLD_NAME = "MANDEVU BRANCJ"
NEW_NAME = "MANDEVU BRANCH"

def main():
    print("=" * 80)
    print("FIX MANDEVU BRANCH GROUPS")
    print("=" * 80)
    
    # Get both branches
    try:
        new_branch = Branch.objects.get(name=NEW_NAME)
        print(f"✓ Found new branch: {new_branch.name} (ID: {new_branch.id})")
    except Branch.DoesNotExist:
        print(f"✗ ERROR: Branch '{NEW_NAME}' not found!")
        return
    
    try:
        old_branch = Branch.objects.get(name=OLD_NAME)
        print(f"✓ Found old branch: {old_branch.name} (ID: {old_branch.id})")
        print(f"  ⚠ This is the branch that should be deleted after migration")
    except Branch.DoesNotExist:
        print(f"✓ Old branch '{OLD_NAME}' doesn't exist (already deleted)")
        old_branch = None
    
    print("\n" + "-" * 80)
    print("CHECKING GROUPS")
    print("-" * 80)
    
    # Find groups linked to old branch - branch is CharField
    if old_branch:
        old_groups = BorrowerGroup.objects.filter(branch=OLD_NAME)
        print(f"\nGroups linked to OLD branch '{OLD_NAME}': {old_groups.count()}")
        for group in old_groups:
            print(f"  - {group.name} (ID: {group.id})")
            print(f"    Officer: {group.assigned_officer.get_full_name() if group.assigned_officer else 'None'}")
            print(f"    Members: {group.members.filter(is_active=True).count()}")
    else:
        old_groups = BorrowerGroup.objects.filter(branch=OLD_NAME)
        print(f"\nGroups with branch name '{OLD_NAME}': {old_groups.count()}")
        for group in old_groups:
            print(f"  - {group.name} (ID: {group.id})")
    
    # Find groups linked to new branch - branch is CharField
    new_groups = BorrowerGroup.objects.filter(branch=NEW_NAME)
    print(f"\nGroups linked to NEW branch '{NEW_NAME}': {new_groups.count()}")
    for group in new_groups:
        print(f"  - {group.name} (ID: {group.id})")
    
    # Check loans
    print("\n" + "-" * 80)
    print("CHECKING LOANS")
    print("-" * 80)
    
    if old_branch:
        # Check if Loan model has branch field
        if hasattr(Loan, 'branch'):
            old_loans = Loan.objects.filter(branch=old_branch)
            print(f"\nLoans linked to OLD branch: {old_loans.count()}")
        else:
            print(f"\nLoan model doesn't have direct branch field")
            # Loans are linked through borrower -> group -> branch
            old_loans_via_group = Loan.objects.filter(
                borrower__group_memberships__group__branch=old_branch,
                borrower__group_memberships__is_active=True
            ).distinct()
            print(f"Loans via groups in OLD branch: {old_loans_via_group.count()}")
    
    if hasattr(Loan, 'branch'):
        new_loans = Loan.objects.filter(branch=new_branch)
        print(f"Loans linked to NEW branch: {new_loans.count()}")
    else:
        new_loans_via_group = Loan.objects.filter(
            borrower__group_memberships__group__branch=new_branch,
            borrower__group_memberships__is_active=True
        ).distinct()
        print(f"Loans via groups in NEW branch: {new_loans_via_group.count()}")
    
    if not old_branch or old_groups.count() == 0:
        print("\n" + "=" * 80)
        print("✓ NO MIGRATION NEEDED")
        print("=" * 80)
        print("\nAll groups are already linked to the correct branch.")
        print(f"MANDEVU BRANCH has {new_groups.count()} groups.")
        return
    
    print("\n" + "=" * 80)
    print("STARTING MIGRATION")
    print("=" * 80)
    
    # Ask for confirmation
    print(f"\nThis will migrate {old_groups.count()} groups from '{OLD_NAME}' to '{NEW_NAME}'")
    print("Press Enter to continue, or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\n✗ Migration cancelled by user")
        return
    
    with transaction.atomic():
        # Update groups - branch is CharField, update string value
        if old_groups.exists():
            count = old_groups.update(branch=NEW_NAME)
            print(f"\n✓ Updated {count} groups to new branch")
        
        # Update loans if they have branch field
        if hasattr(Loan, 'branch'):
            old_loans = Loan.objects.filter(branch=old_branch) if old_branch else Loan.objects.none()
            if old_loans.exists():
                count = old_loans.update(branch=new_branch)
                print(f"✓ Updated {count} loans to new branch")
    
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    # Verify
    new_groups = BorrowerGroup.objects.filter(branch=NEW_NAME)
    old_groups = BorrowerGroup.objects.filter(branch=OLD_NAME)
    
    print(f"\nAfter migration:")
    print(f"  - Groups in NEW branch '{NEW_NAME}': {new_groups.count()}")
    print(f"  - Groups in OLD branch '{OLD_NAME}': {old_groups.count()}")
    
    if hasattr(Loan, 'branch'):
        new_loans = Loan.objects.filter(branch=new_branch)
        old_loans = Loan.objects.filter(branch=old_branch) if old_branch else Loan.objects.none()
        print(f"  - Loans in NEW branch: {new_loans.count()}")
        print(f"  - Loans in OLD branch: {old_loans.count()}")
    
    print("\n" + "=" * 80)
    print("✓ MIGRATION COMPLETE")
    print("=" * 80)
    
    if old_branch and old_groups.count() == 0:
        print("\n⚠ IMPORTANT: You should now DELETE the old branch from admin panel:")
        print(f"   1. Go to Admin Dashboard → Branches")
        print(f"   2. Find '{OLD_NAME}' (ID: {old_branch.id})")
        print(f"   3. Click 'Deactivate' or 'Delete'")
        print(f"   4. This will prevent confusion with duplicate branch names")
    
    print("\nNext steps:")
    print("1. Refresh the groups page")
    print("2. All groups should now show 'MANDEVU BRANCH'")
    print("3. Loans should be visible under the correct branch")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
