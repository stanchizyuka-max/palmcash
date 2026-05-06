#!/usr/bin/env python
"""
Restore MANDEVU BRANCH Data
============================
This script restores all data after the branch name was changed from "MANDEVU BRANCJ" to "MANDEVU BRANCH"
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.db import transaction
from clients.models import Branch, BorrowerGroup, OfficerAssignment
from accounts.models import User
from loans.models import Loan, DailyVault, WeeklyVault, BranchSavings
from expenses.models import VaultTransaction

OLD_NAME = "MANDEVU BRANCJ"
NEW_NAME = "MANDEVU BRANCH"

def main():
    print("=" * 80)
    print("MANDEVU BRANCH DATA RESTORATION")
    print("=" * 80)
    
    # Get the branch
    try:
        branch = Branch.objects.get(name=NEW_NAME)
        print(f"✓ Found branch: {branch.name} (ID: {branch.id})")
    except Branch.DoesNotExist:
        print(f"✗ ERROR: Branch '{NEW_NAME}' not found!")
        return
    
    print("\n" + "-" * 80)
    print("CHECKING CURRENT STATE")
    print("-" * 80)
    
    # Check officer assignments
    officer_assignments = OfficerAssignment.objects.filter(branch=NEW_NAME)
    print(f"\nOfficer Assignments: {officer_assignments.count()}")
    for oa in officer_assignments:
        print(f"  - {oa.officer.get_full_name()}")
    
    # Check groups
    groups = BorrowerGroup.objects.filter(branch=branch)
    print(f"\nBorrower Groups: {groups.count()}")
    for group in groups[:5]:
        print(f"  - {group.name}")
    
    # Check loans
    loans = Loan.objects.filter(branch=branch) if hasattr(Loan, 'branch') else Loan.objects.none()
    print(f"\nLoans: {loans.count()}")
    
    # Check vault transactions
    vault_txs = VaultTransaction.objects.filter(branch=NEW_NAME)
    print(f"\nVault Transactions: {vault_txs.count()}")
    
    # Check for old name references
    old_vault_txs = VaultTransaction.objects.filter(branch=OLD_NAME)
    old_groups = BorrowerGroup.objects.filter(branch=branch)  # Groups use ForeignKey to Branch
    old_officer_assignments = OfficerAssignment.objects.filter(branch=OLD_NAME)  # branch is CharField
    
    print(f"\n" + "-" * 80)
    print("CHECKING FOR OLD NAME REFERENCES")
    print("-" * 80)
    print(f"\nVault Transactions with old name: {old_vault_txs.count()}")
    print(f"Officer Assignments with old name: {old_officer_assignments.count()}")
    print(f"Groups for this branch: {old_groups.count()}")
    
    if old_vault_txs.count() == 0 and old_officer_assignments.count() == 0:
        print("\n✓ No old name references found. Data already migrated.")
        print("\nThe issue is that MANDEVU BRANCH has:")
        print(f"  - {officer_assignments.count()} Officer Assignments")
        print(f"  - {groups.count()} Borrower Groups")
        print(f"  - {loans.count()} Loans")
        print(f"  - {vault_txs.count()} Vault Transactions")
        
        if officer_assignments.count() == 0 and groups.count() == 0:
            print("\nThis means:")
            print("  1. Officers were never assigned to this branch, OR")
            print("  2. Groups were never created for this branch, OR")
            print("  3. Data was deleted/lost during the rename")
        
        # Check all officer assignments
        print(f"\n" + "-" * 80)
        print("ALL OFFICER ASSIGNMENTS IN SYSTEM")
        print("-" * 80)
        all_assignments = OfficerAssignment.objects.all()
        print(f"\nTotal: {all_assignments.count()}")
        for oa in all_assignments:
            # branch is stored as a string, not a ForeignKey
            branch_name = oa.branch if oa.branch else 'No Branch'
            print(f"  - {oa.officer.get_full_name()} → {branch_name}")
        
        # Check all groups
        print(f"\n" + "-" * 80)
        print("ALL BORROWER GROUPS IN SYSTEM")
        print("-" * 80)
        all_groups = BorrowerGroup.objects.all()
        print(f"\nTotal: {all_groups.count()}")
        for group in all_groups[:20]:
            print(f"  - {group.name} → {group.branch.name if group.branch else 'No Branch'}")
        
        return
    
    print(f"\n" + "=" * 80)
    print("STARTING DATA MIGRATION")
    print("=" * 80)
    
    with transaction.atomic():
        # 1. Update VaultTransaction
        if old_vault_txs.exists():
            count = old_vault_txs.update(branch=NEW_NAME)
            print(f"\n✓ Updated {count} vault transactions")
        
        # 2. Update OfficerAssignment (branch is CharField)
        if old_officer_assignments.exists():
            count = old_officer_assignments.update(branch=NEW_NAME)
            print(f"✓ Updated {count} officer assignments")
        
        # 3. Update User managed_branch (ForeignKey to Branch)
        managers = User.objects.filter(role='manager', managed_branch__name=OLD_NAME)
        if managers.exists():
            for manager in managers:
                manager.managed_branch = branch
                manager.save(update_fields=['managed_branch'])
            print(f"✓ Updated {managers.count()} manager assignments")
        
        # 4. Update Loans if they have branch field
        if hasattr(Loan, 'branch'):
            old_loans = Loan.objects.filter(branch__name=OLD_NAME)
            if old_loans.exists():
                count = old_loans.update(branch=branch)
                print(f"✓ Updated {count} loans")
        
        # 5. Update Vaults
        old_daily = DailyVault.objects.filter(branch__name=OLD_NAME)
        if old_daily.exists():
            count = old_daily.update(branch=branch)
            print(f"✓ Updated {count} daily vaults")
        
        old_weekly = WeeklyVault.objects.filter(branch__name=OLD_NAME)
        if old_weekly.exists():
            count = old_weekly.update(branch=branch)
            print(f"✓ Updated {count} weekly vaults")
        
        # 6. Update Savings
        old_savings = BranchSavings.objects.filter(branch__name=OLD_NAME)
        if old_savings.exists():
            count = old_savings.update(branch=branch)
            print(f"✓ Updated {count} savings records")
    
    print(f"\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    # Verify the changes
    officer_assignments = OfficerAssignment.objects.filter(branch=NEW_NAME)
    groups = BorrowerGroup.objects.filter(branch=branch)
    vault_txs = VaultTransaction.objects.filter(branch=NEW_NAME)
    
    print(f"\nMANDEVU BRANCH now has:")
    print(f"  - Officer Assignments: {officer_assignments.count()}")
    print(f"  - Borrower Groups: {groups.count()}")
    print(f"  - Vault Transactions: {vault_txs.count()}")
    
    # Check if old branch still exists
    old_branch_exists = Branch.objects.filter(name=OLD_NAME).exists()
    if old_branch_exists:
        print(f"\n⚠ WARNING: Old branch '{OLD_NAME}' still exists in database!")
        print(f"  You should delete it from the admin panel.")
    
    print("\n" + "=" * 80)
    print("✓ RESTORATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Refresh the branches page to see updated officer count")
    print("2. Check vault transactions are visible")
    print("3. Verify groups and loans are showing correctly")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
