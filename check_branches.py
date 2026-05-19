#!/usr/bin/env python
"""
Check branches in the system
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.contrib.auth import get_user_model
from loans.models import OfficerAssignment
from clients.models import BorrowerGroup

User = get_user_model()

print("=" * 70)
print("CHECKING BRANCHES IN SYSTEM")
print("=" * 70)
print()

# Check OfficerAssignment branches
print("1. Branches in OfficerAssignment:")
assignments = OfficerAssignment.objects.all()
print(f"   Total assignments: {assignments.count()}")
for assignment in assignments[:10]:
    print(f"   - Officer: {assignment.officer.username}, Branch: {assignment.branch}")
print()

# Check unique branches
branches = OfficerAssignment.objects.values_list('branch', flat=True).distinct()
print(f"2. Unique branches: {branches.count()}")
for branch in branches:
    print(f"   - {branch}")
print()

# Check BorrowerGroup branches
print("3. Branches in BorrowerGroup:")
groups = BorrowerGroup.objects.all()
print(f"   Total groups: {groups.count()}")
for group in groups[:10]:
    print(f"   - Group: {group.name}, Branch: {group.branch}")
print()

# Check sample borrowers
print("4. Sample borrowers and their branches:")
borrowers = User.objects.filter(role='borrower')[:10]
for borrower in borrowers:
    branch = borrower.get_branch()
    print(f"   - {borrower.get_full_name()}: {branch}")
    if branch == 'N/A':
        print(f"     * assigned_officer: {borrower.assigned_officer}")
        if borrower.assigned_officer:
            print(f"     * officer branch: {borrower.assigned_officer.get_branch()}")
print()

print("=" * 70)
