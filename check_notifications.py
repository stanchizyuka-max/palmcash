#!/usr/bin/env python
"""
Check notifications to see which branches they're from and who's receiving them
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

# Django imports
from django.db.models import Q, Count
from notifications.models import Notification
from accounts.models import User

print("\n" + "="*70)
print("NOTIFICATION BRANCH ANALYSIS")
print("="*70)

# Get a sample of recent notifications
recent_notifications = Notification.objects.select_related(
    'recipient', 'loan', 'loan__loan_officer', 'loan__loan_officer__officer_assignment'
).order_by('-created_at')[:20]

print(f"\n📋 RECENT NOTIFICATIONS (Last 20):")
print(f"{'='*70}")

for notif in recent_notifications:
    recipient_role = notif.recipient.role if notif.recipient else 'Unknown'
    recipient_branch = 'N/A'
    
    if notif.recipient:
        if notif.recipient.role == 'manager' and hasattr(notif.recipient, 'managed_branch'):
            recipient_branch = notif.recipient.managed_branch.name
        elif notif.recipient.role == 'loan_officer' and hasattr(notif.recipient, 'officer_assignment'):
            recipient_branch = notif.recipient.officer_assignment.branch
        elif notif.recipient.role == 'admin':
            recipient_branch = 'ALL (Admin)'
    
    loan_branch = 'N/A'
    if notif.loan and notif.loan.loan_officer and hasattr(notif.loan.loan_officer, 'officer_assignment'):
        loan_branch = notif.loan.loan_officer.officer_assignment.branch
    
    match = '✅' if recipient_branch == loan_branch or recipient_branch == 'ALL (Admin)' else '❌'
    
    print(f"\n{match} Notification ID: {notif.id}")
    print(f"   Created: {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Subject: {notif.subject[:50]}...")
    print(f"   Recipient: {notif.recipient.get_full_name() if notif.recipient else 'Unknown'} ({recipient_role})")
    print(f"   Recipient Branch: {recipient_branch}")
    if notif.loan:
        print(f"   Loan: {notif.loan.application_number}")
        print(f"   Loan Branch: {loan_branch}")
        print(f"   Match: {'YES' if match == '✅' else 'NO - WRONG BRANCH!'}")

# Count notifications by recipient role
print(f"\n{'='*70}")
print(f"NOTIFICATION COUNT BY ROLE:")
print(f"{'='*70}")

role_counts = Notification.objects.values('recipient__role').annotate(
    count=Count('id')
).order_by('-count')

for item in role_counts:
    role = item['recipient__role'] or 'Unknown'
    count = item['count']
    print(f"   {role}: {count} notifications")

# Check for notifications without loan (might not be filtered)
print(f"\n{'='*70}")
print(f"NOTIFICATIONS WITHOUT LOAN:")
print(f"{'='*70}")

no_loan_count = Notification.objects.filter(loan__isnull=True).count()
print(f"   Total: {no_loan_count} notifications")

if no_loan_count > 0:
    print(f"\n   ⚠️  These notifications cannot be filtered by branch!")
    print(f"   They might be system-wide notifications.")
    
    no_loan_notifs = Notification.objects.filter(loan__isnull=True).order_by('-created_at')[:5]
    for notif in no_loan_notifs:
        print(f"\n   - ID: {notif.id}")
        print(f"     Subject: {notif.subject}")
        print(f"     Recipient: {notif.recipient.get_full_name() if notif.recipient else 'Unknown'}")

# Check specific user's notifications
print(f"\n{'='*70}")
print(f"CHECK SPECIFIC USER:")
print(f"{'='*70}")

username = input("\nEnter username to check (or press Enter to skip): ").strip()

if username:
    try:
        user = User.objects.get(username=username)
        print(f"\n✅ Found user: {user.get_full_name()} ({user.role})")
        
        user_branch = 'N/A'
        if user.role == 'manager' and hasattr(user, 'managed_branch'):
            user_branch = user.managed_branch.name
        elif user.role == 'loan_officer' and hasattr(user, 'officer_assignment'):
            user_branch = user.officer_assignment.branch
        elif user.role == 'admin':
            user_branch = 'ALL (Admin)'
        
        print(f"   Branch: {user_branch}")
        
        user_notifs = Notification.objects.filter(recipient=user).select_related(
            'loan', 'loan__loan_officer', 'loan__loan_officer__officer_assignment'
        ).order_by('-created_at')[:10]
        
        print(f"\n   Recent notifications ({user_notifs.count()}):")
        
        wrong_branch_count = 0
        for notif in user_notifs:
            loan_branch = 'N/A'
            if notif.loan and notif.loan.loan_officer and hasattr(notif.loan.loan_officer, 'officer_assignment'):
                loan_branch = notif.loan.loan_officer.officer_assignment.branch
            
            match = '✅' if user_branch == loan_branch or user_branch == 'ALL (Admin)' or not notif.loan else '❌'
            if match == '❌':
                wrong_branch_count += 1
            
            print(f"\n   {match} {notif.subject[:40]}...")
            print(f"      Created: {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
            if notif.loan:
                print(f"      Loan: {notif.loan.application_number} (Branch: {loan_branch})")
        
        if wrong_branch_count > 0:
            print(f"\n   ⚠️  Found {wrong_branch_count} notification(s) from wrong branch!")
            print(f"   These were likely created before the fix was deployed.")
        else:
            print(f"\n   ✅ All notifications are from the correct branch!")
            
    except User.DoesNotExist:
        print(f"\n❌ User '{username}' not found")

print(f"\n{'='*70}\n")
