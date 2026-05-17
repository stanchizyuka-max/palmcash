#!/usr/bin/env python
"""
Test client visibility for different user roles
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

# Django imports
from django.db.models import Q
from accounts.models import User
from clients.models import BorrowerGroup

print("\n" + "="*70)
print("TEST CLIENT VISIBILITY BY ROLE")
print("="*70)

# Get KUKU officers
kuku_officers = User.objects.filter(
    role='loan_officer',
    officer_assignment__branch__iexact='KUKU'
)

print(f"\n📋 KUKU Officers ({kuku_officers.count()}):")
for officer in kuku_officers:
    print(f"   - {officer.get_full_name()} (ID: {officer.id})")

# Get KUKU manager
kuku_manager = User.objects.filter(
    role='manager',
    managed_branch__name__iexact='KUKU'
).first()

if kuku_manager:
    print(f"\n👤 KUKU Manager: {kuku_manager.get_full_name()} (ID: {kuku_manager.id})")
else:
    print(f"\n⚠️  No KUKU manager found")

# Get admin
admin = User.objects.filter(role='admin').first()
if admin:
    print(f"\n👑 Admin: {admin.get_full_name()} (ID: {admin.id})")

print(f"\n{'='*70}")
print(f"TESTING VISIBILITY:")
print(f"{'='*70}")

# Test 1: Admin view (should see all)
print(f"\n1️⃣  ADMIN VIEW:")
admin_queryset = User.objects.filter(role='borrower', is_active=True)
print(f"   Total borrowers visible: {admin_queryset.count()}")

kuku_in_admin = admin_queryset.filter(
    assigned_officer__officer_assignment__branch__iexact='KUKU'
).count()
print(f"   KUKU borrowers: {kuku_in_admin}")

# Test 2: Manager view
if kuku_manager:
    print(f"\n2️⃣  MANAGER VIEW (KUKU Manager):")
    try:
        manager_branch = kuku_manager.managed_branch.name
        print(f"   Manager's branch: {manager_branch}")
        
        manager_queryset = User.objects.filter(role='borrower', is_active=True).filter(
            Q(group_memberships__group__branch__iexact=manager_branch, group_memberships__is_active=True) |
            Q(assigned_officer__officer_assignment__branch__iexact=manager_branch)
        ).distinct()
        
        print(f"   Total borrowers visible: {manager_queryset.count()}")
        
        # Show sample
        print(f"\n   Sample borrowers:")
        for borrower in manager_queryset[:5]:
            officer = borrower.assigned_officer
            officer_name = officer.get_full_name() if officer else 'None'
            officer_branch = 'N/A'
            if officer and hasattr(officer, 'officer_assignment'):
                officer_branch = officer.officer_assignment.branch
            print(f"      - {borrower.get_full_name()} (Officer: {officer_name}, Branch: {officer_branch})")
        
        if manager_queryset.count() > 5:
            print(f"      ... and {manager_queryset.count() - 5} more")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Test 3: Loan Officer view
if kuku_officers.exists():
    test_officer = kuku_officers.first()
    print(f"\n3️⃣  LOAN OFFICER VIEW ({test_officer.get_full_name()}):")
    
    officer_queryset = User.objects.filter(role='borrower', is_active=True).filter(
        Q(assigned_officer=test_officer) |
        Q(group_memberships__group__assigned_officer=test_officer, group_memberships__is_active=True)
    ).distinct()
    
    print(f"   Total borrowers visible: {officer_queryset.count()}")
    
    # Show sample
    print(f"\n   Sample borrowers:")
    for borrower in officer_queryset[:5]:
        print(f"      - {borrower.get_full_name()}")
    
    if officer_queryset.count() > 5:
        print(f"      ... and {officer_queryset.count() - 5} more")

# Test 4: Check for borrowers with no assigned officer
print(f"\n{'='*70}")
print(f"CHECKING FOR ISSUES:")
print(f"{'='*70}")

no_officer = User.objects.filter(role='borrower', is_active=True, assigned_officer__isnull=True)
print(f"\n⚠️  Borrowers with NO assigned officer: {no_officer.count()}")
if no_officer.exists():
    for borrower in no_officer[:5]:
        print(f"   - {borrower.get_full_name()} (ID: {borrower.id})")

# Check for KUKU borrowers specifically
kuku_borrowers = User.objects.filter(
    role='borrower',
    is_active=True,
    assigned_officer__officer_assignment__branch__iexact='KUKU'
)

print(f"\n✅ Total KUKU borrowers (by assigned_officer): {kuku_borrowers.count()}")

# Check if any are inactive
inactive_kuku = User.objects.filter(
    role='borrower',
    is_active=False,
    assigned_officer__officer_assignment__branch__iexact='KUKU'
)

if inactive_kuku.exists():
    print(f"\n⚠️  INACTIVE KUKU borrowers: {inactive_kuku.count()}")
    for borrower in inactive_kuku:
        print(f"   - {borrower.get_full_name()} (ID: {borrower.id}) - INACTIVE")

print(f"\n{'='*70}")
print(f"SUMMARY:")
print(f"{'='*70}")

print(f"\n✅ All roles should see KUKU clients:")
print(f"   - Admins: See all {admin_queryset.count()} borrowers (including {kuku_in_admin} from KUKU)")
if kuku_manager:
    print(f"   - KUKU Manager: Should see {manager_queryset.count()} borrowers")
if kuku_officers.exists():
    print(f"   - KUKU Officers: Each sees their assigned clients")

print(f"\n💡 If clients are still missing:")
print(f"   1. Check browser cache (Ctrl+F5)")
print(f"   2. Check pagination (clients might be on page 2, 3, etc.)")
print(f"   3. Check if any filters are applied in the UI")
print(f"   4. Check if borrowers are marked as inactive")

print(f"\n{'='*70}\n")
