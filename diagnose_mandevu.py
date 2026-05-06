#!/usr/bin/env python
"""
Diagnose MANDEVU BRANCH Issue
==============================
Check all branches and groups to understand the current state
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from clients.models import Branch, BorrowerGroup

def main():
    print("=" * 80)
    print("MANDEVU BRANCH DIAGNOSTIC")
    print("=" * 80)
    
    # Check all branches
    print("\n" + "-" * 80)
    print("ALL BRANCHES IN DATABASE")
    print("-" * 80)
    all_branches = Branch.objects.all()
    print(f"\nTotal branches: {all_branches.count()}")
    for branch in all_branches:
        print(f"\nBranch: {branch.name}")
        print(f"  ID: {branch.id}")
        print(f"  Code: {branch.code}")
        print(f"  Active: {branch.is_active}")
        
        # Count groups
        groups = BorrowerGroup.objects.filter(branch=branch)
        print(f"  Groups: {groups.count()}")
        if groups.exists():
            for group in groups:
                print(f"    - {group.name} (ID: {group.id})")
    
    # Check for groups with "Gray" and "Liverpool"
    print("\n" + "-" * 80)
    print("SEARCHING FOR GRAY AND LIVERPOOL GROUPS")
    print("-" * 80)
    
    gray = BorrowerGroup.objects.filter(name__icontains='Gray')
    print(f"\nGroups matching 'Gray': {gray.count()}")
    for g in gray:
        print(f"  - {g.name} (ID: {g.id})")
        print(f"    Branch: {g.branch.name if g.branch else 'None'} (ID: {g.branch.id if g.branch else 'N/A'})")
        print(f"    Branch Active: {g.branch.is_active if g.branch else 'N/A'}")
        print(f"    Officer: {g.assigned_officer.get_full_name() if g.assigned_officer else 'None'}")
    
    liverpool = BorrowerGroup.objects.filter(name__icontains='Liverpool')
    print(f"\nGroups matching 'Liverpool': {liverpool.count()}")
    for g in liverpool:
        print(f"  - {g.name} (ID: {g.id})")
        print(f"    Branch: {g.branch.name if g.branch else 'None'} (ID: {g.branch.id if g.branch else 'N/A'})")
        print(f"    Branch Active: {g.branch.is_active if g.branch else 'N/A'}")
        print(f"    Officer: {g.assigned_officer.get_full_name() if g.assigned_officer else 'None'}")
    
    # Check for inactive branches
    print("\n" + "-" * 80)
    print("INACTIVE BRANCHES")
    print("-" * 80)
    inactive = Branch.objects.filter(is_active=False)
    print(f"\nTotal inactive branches: {inactive.count()}")
    for branch in inactive:
        print(f"\nBranch: {branch.name}")
        print(f"  ID: {branch.id}")
        print(f"  Code: {branch.code}")
        groups = BorrowerGroup.objects.filter(branch=branch)
        print(f"  Groups: {groups.count()}")
        if groups.exists():
            for group in groups:
                print(f"    - {group.name}")
    
    # Check MANDEVU branches specifically
    print("\n" + "-" * 80)
    print("MANDEVU BRANCHES (ACTIVE AND INACTIVE)")
    print("-" * 80)
    mandevu_branches = Branch.objects.filter(name__icontains='MANDEVU')
    print(f"\nTotal MANDEVU branches: {mandevu_branches.count()}")
    for branch in mandevu_branches:
        print(f"\nBranch: {branch.name}")
        print(f"  ID: {branch.id}")
        print(f"  Code: {branch.code}")
        print(f"  Active: {branch.is_active}")
        groups = BorrowerGroup.objects.filter(branch=branch)
        print(f"  Groups: {groups.count()}")
        if groups.exists():
            for group in groups:
                print(f"    - {group.name} (ID: {group.id})")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
