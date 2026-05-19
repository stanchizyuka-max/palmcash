#!/usr/bin/env python
"""
Test script to verify search and filter functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Q
from notifications.models import Notification
from loans.models import OfficerAssignment

User = get_user_model()

def test_user_search():
    """Test user search functionality"""
    print("=" * 70)
    print("TEST USER SEARCH FUNCTIONALITY")
    print("=" * 70)
    print()
    
    # Test 1: Search by phone number
    print("Test 1: Search by phone number (0977)")
    users = User.objects.filter(phone_number__icontains='0977')
    print(f"  Found {users.count()} users with phone containing '0977'")
    for user in users[:3]:
        print(f"  - {user.get_full_name()} ({user.phone_number})")
    print()
    
    # Test 2: Search by name
    print("Test 2: Search by name (Elizabeth)")
    users = User.objects.filter(
        Q(first_name__icontains='Elizabeth') |
        Q(last_name__icontains='Elizabeth')
    )
    print(f"  Found {users.count()} users with name containing 'Elizabeth'")
    for user in users[:3]:
        print(f"  - {user.get_full_name()} ({user.username})")
    print()
    
    # Test 3: Filter by branch
    print("Test 3: Filter by branch (KUKU)")
    users = User.objects.filter(
        Q(officer_assignment__branch__iexact='KUKU') |
        Q(assigned_officer__officer_assignment__branch__iexact='KUKU') |
        Q(group_memberships__group__branch__iexact='KUKU', group_memberships__is_active=True)
    ).distinct()
    print(f"  Found {users.count()} users in KUKU branch")
    print()
    
    # Test 4: Filter by status
    print("Test 4: Filter by status (Active)")
    active_users = User.objects.filter(is_active=True)
    inactive_users = User.objects.filter(is_active=False)
    print(f"  Active users: {active_users.count()}")
    print(f"  Inactive users: {inactive_users.count()}")
    print()
    
    # Test 5: Combined filters
    print("Test 5: Combined filters (Borrowers in KUKU, Active)")
    users = User.objects.filter(
        role='borrower',
        is_active=True
    ).filter(
        Q(assigned_officer__officer_assignment__branch__iexact='KUKU') |
        Q(group_memberships__group__branch__iexact='KUKU', group_memberships__is_active=True)
    ).distinct()
    print(f"  Found {users.count()} active borrowers in KUKU")
    print()

def test_notification_filters():
    """Test notification filter functionality"""
    print("=" * 70)
    print("TEST NOTIFICATION FILTER FUNCTIONALITY")
    print("=" * 70)
    print()
    
    # Get an admin user for testing
    admin = User.objects.filter(role='admin').first()
    if not admin:
        print("  ⚠️  No admin user found. Skipping notification tests.")
        return
    
    # Test 1: All notifications
    print(f"Test 1: All notifications for {admin.username}")
    all_notifications = Notification.objects.filter(recipient=admin)
    print(f"  Total notifications: {all_notifications.count()}")
    print()
    
    # Test 2: Unread notifications
    print("Test 2: Unread notifications")
    unread = all_notifications.filter(status__in=['pending', 'sent', 'delivered'])
    print(f"  Unread: {unread.count()}")
    print()
    
    # Test 3: Read notifications
    print("Test 3: Read notifications")
    read = all_notifications.filter(status='read')
    print(f"  Read: {read.count()}")
    print()
    
    # Test 4: Filter by branch (KUKU)
    print("Test 4: Filter by branch (KUKU)")
    branch_notifications = all_notifications.filter(
        Q(loan__borrower__assigned_officer__officer_assignment__branch__iexact='KUKU') |
        Q(loan__borrower__group_memberships__group__branch__iexact='KUKU', loan__borrower__group_memberships__is_active=True) |
        Q(payment__loan__borrower__assigned_officer__officer_assignment__branch__iexact='KUKU') |
        Q(payment__loan__borrower__group_memberships__group__branch__iexact='KUKU', payment__loan__borrower__group_memberships__is_active=True)
    ).distinct()
    print(f"  KUKU branch notifications: {branch_notifications.count()}")
    print()
    
    # Test 5: Combined filters (Unread from KUKU)
    print("Test 5: Combined filters (Unread from KUKU)")
    combined = branch_notifications.filter(status__in=['pending', 'sent', 'delivered'])
    print(f"  Unread KUKU notifications: {combined.count()}")
    print()

def test_branches_list():
    """Test branches list for dropdown"""
    print("=" * 70)
    print("TEST BRANCHES LIST")
    print("=" * 70)
    print()
    
    branches = OfficerAssignment.objects.values_list('branch', flat=True).distinct().order_by('branch')
    print(f"Available branches ({branches.count()}):")
    for branch in branches:
        print(f"  - {branch}")
    print()

def main():
    """Run all tests"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "SEARCH & FILTER TESTS" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        test_user_search()
        test_notification_filters()
        test_branches_list()
        
        print("=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Test the filters in the web interface")
        print("2. Try searching for users by name, phone, email")
        print("3. Try filtering notifications by branch and status")
        print("4. Verify pagination preserves filters")
        print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR DURING TESTS")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
