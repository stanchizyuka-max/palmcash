#!/usr/bin/env python
"""
Clean up notifications that were sent to the wrong branch
(created before the branch filtering fix was deployed)
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'palmcash.settings')
django.setup()

# Django imports
from django.db.models import Q
from notifications.models import Notification
from accounts.models import User

print("\n" + "="*70)
print("CLEANUP WRONG-BRANCH NOTIFICATIONS")
print("="*70)

# Find notifications where recipient branch doesn't match loan branch
wrong_branch_notifications = []

notifications = Notification.objects.select_related(
    'recipient', 'loan', 'loan__loan_officer', 'loan__loan_officer__officer_assignment'
).filter(
    loan__isnull=False  # Only check loan-related notifications
).order_by('-created_at')

print(f"\n🔍 Checking {notifications.count()} loan-related notifications...")

for notif in notifications:
    # Skip if no recipient
    if not notif.recipient:
        continue
    
    # Skip admins (they should see all branches)
    if notif.recipient.role == 'admin':
        continue
    
    # Skip borrowers (they should see their own loans)
    if notif.recipient.role == 'borrower':
        continue
    
    # Get recipient's branch
    recipient_branch = None
    if notif.recipient.role == 'manager' and hasattr(notif.recipient, 'managed_branch'):
        recipient_branch = notif.recipient.managed_branch.name
    elif notif.recipient.role == 'loan_officer' and hasattr(notif.recipient, 'officer_assignment'):
        recipient_branch = notif.recipient.officer_assignment.branch
    
    # Get loan's branch
    loan_branch = None
    if notif.loan and notif.loan.loan_officer and hasattr(notif.loan.loan_officer, 'officer_assignment'):
        loan_branch = notif.loan.loan_officer.officer_assignment.branch
    
    # Check if branches match (case-insensitive)
    if recipient_branch and loan_branch:
        if recipient_branch.lower() != loan_branch.lower():
            wrong_branch_notifications.append({
                'notification': notif,
                'recipient_branch': recipient_branch,
                'loan_branch': loan_branch
            })

print(f"\n📊 RESULTS:")
print(f"   Total checked: {notifications.count()}")
print(f"   Wrong branch: {len(wrong_branch_notifications)}")

if not wrong_branch_notifications:
    print(f"\n✅ No wrong-branch notifications found!")
    print(f"   All notifications are correctly filtered.")
    exit()

# Show sample of wrong notifications
print(f"\n❌ WRONG-BRANCH NOTIFICATIONS:")
print(f"{'='*70}")

for i, item in enumerate(wrong_branch_notifications[:10], 1):
    notif = item['notification']
    print(f"\n{i}. ID: {notif.id}")
    print(f"   Created: {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Subject: {notif.subject[:50]}...")
    print(f"   Recipient: {notif.recipient.get_full_name()} ({notif.recipient.role})")
    print(f"   Recipient Branch: {item['recipient_branch']}")
    print(f"   Loan: {notif.loan.application_number}")
    print(f"   Loan Branch: {item['loan_branch']}")

if len(wrong_branch_notifications) > 10:
    print(f"\n   ... and {len(wrong_branch_notifications) - 10} more")

# Ask for confirmation
print(f"\n{'='*70}")
print(f"READY TO DELETE")
print(f"{'='*70}")

print(f"\n⚠️  This will delete {len(wrong_branch_notifications)} notification(s)")
print(f"   These are notifications sent to staff in the wrong branch.")
print(f"   This will NOT affect:")
print(f"   - Admin notifications (they see all branches)")
print(f"   - Borrower notifications (they see their own loans)")
print(f"   - Correctly filtered notifications")

response = input(f"\nDelete {len(wrong_branch_notifications)} wrong-branch notifications? (yes/no): ")

if response.lower() != 'yes':
    print(f"\n❌ Aborted. No notifications deleted.")
    exit()

# Delete the notifications
print(f"\n🗑️  Deleting notifications...")

deleted_count = 0
for item in wrong_branch_notifications:
    notif = item['notification']
    notif.delete()
    deleted_count += 1

print(f"\n✅ DONE!")
print(f"   Deleted: {deleted_count} notification(s)")
print(f"\n💡 From now on, all NEW notifications will be correctly filtered by branch.")
print(f"   Officers and managers will only see notifications for their branch.")

print(f"\n{'='*70}\n")
